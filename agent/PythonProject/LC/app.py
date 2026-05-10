# python app.py
#uv sync --active
import os
import json
from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from typing import List, Dict
import re
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'
# 配置session使用服务器端存储，避免cookie大小限制
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session')
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # session过期时间1小时
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 最大请求大小16MB
app.config['SESSION_COOKIE_NAME'] = 'session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # 在开发环境中设置为False

# 创建session存储目录
if not os.path.exists(app.config['SESSION_FILE_DIR']):
    os.makedirs(app.config['SESSION_FILE_DIR'])

# 初始化flask-session
Session(app)

# 初始化模型 - DeepSeek
model = init_chat_model(
    model="deepseek-chat",
    model_provider="openai",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    temperature=1.2,
)

# 初始化多模态模型 - 千问(用于漫画生成)
# 只有在设置了DASHSCOPE_API_KEY时才初始化
qwen_model = None
if os.getenv("DASHSCOPE_API_KEY"):
    qwen_model = init_chat_model(
        model="qwen-vl-max",
        model_provider="openai",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature=0.8,
    )
else:
    print("警告: DASHSCOPE_API_KEY 未设置，漫画生成功能不可用")

# 导入DashScope图片生成API
try:
    from dashscope import ImageSynthesis
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    print("警告: dashscope包未安装，图片生成功能不可用")

# 定义故事智能体的系统提示
STORY_PROMPT = """
你是一个互动故事叙述者，正在讲述一个用户自定义背景的冒险故事。

**严格规则：**
1. **只输出故事情节本身**，不要添加任何额外内容
2. **禁止生成章节标题**（如"第一章"、"场景一"等）
3. **禁止添加说明性文字**（如"以下是故事"、"你来到..."等引导语）
4. 每次只推进一小段情节（80-150字），确保情节连贯流畅
5. 每段情节后必须给出4个选项供用户选择：前3个由AI生成，第4个固定为【选项4】自定义行动
6. 选项格式必须严格为：【选项1】描述内容 【选项2】描述内容 【选项3】描述内容 【选项4】自定义行动
7. 每个选项的描述要简洁明了（不超过20字）
8. 用户的选择会影响后续情节和结局
9. 故事要有多个可能的结局（成功、失败、特殊结局等），**坏结局应该罕见且合理**
10. 保持故事的紧张感和趣味性
11. 不要一次性讲完整个故事，要循序渐进
12. 确保前三个选项都有明显的区别
13. **极其重要**：你必须严格根据用户的实际选择来推进情节，绝对不能臆造用户未做的选择
14. **极其重要**：如果用户说"我选择：XXX"，你只能基于这个选择继续故事，不能假设用户选择了其他选项
15. **极其重要**：在生成新内容前，先回顾之前的对话历史，确保情节连贯
16. **极其重要**：如果用户的选择与之前的选项不完全一致，也要尽量理解用户意图并继续故事
17. 记住用户之前的所有选择，让故事连贯发展
18. 根据历史选择调整情节走向，体现因果关系
19. 当故事达到自然结局时，在回复末尾添加特殊标记：
    - 成功结局：【结局:成功】
    - 失败结局：【结局:失败】
    - 特殊结局：【结局:特殊】
    - 坏结局：【结局:坏结局】
20. 结局章节不需要再提供选项，直接讲述最终结果
21. 根据用户的选择序列合理判断何时应该结束故事，不要无限延续
22. **道具系统**：故事中会出现各种道具，玩家可以选择使用。道具可能帮助也可能阻碍玩家
23. 当出现可以使用道具的时机，在选项中可以包含道具使用选项，格式：【选项X】使用[道具名]...
24. 记录玩家获得的道具，并在合适的时机提示可以使用
25. **坏结局触发条件**：坏结局应该由AI根据故事情节和用户选择自然判断，考虑以下因素：
    - 玩家连续做出明显错误的选择（至少5次以上）
    - 玩家忽视明确的危险警告，一意孤行
    - 玩家做出极度鲁莽或致命的行为（如跳崖、自杀等）
    - 故事已经进行了足够长的时间（至少10章以上），需要自然收尾
    - 玩家的行动导致无法挽回的后果
    - **重要**：坏结局应该是小概率事件，要符合故事逻辑，不要突兀
    - **关键**：即使是自杀行为，也要通过故事情节自然展现，而不是机械触发
26. **死亡场景描写**：当触发死亡结局时：
    - 要描写死亡的過程和原因，让玩家理解为什么会导致死亡
    - 要有情感冲击力，让玩家感受到选择的后果
    - 要符合故事背景和情节发展，不要生硬
    - 例如：“你纵身跳下悬崖，风声在耳边呼啸。这一刻，你想起了很多...身体撞击岩石的瞬间，一切归于黑暗。【结局:坏结局】”
27. **关键**：每次生成都要确保故事能够顺利推进，不要因为理解偏差而中断
28. **关键**：如果用户输入模糊，请按照最合理的解释继续故事，而不是停止
29. **难度控制**：
    - 简单难度：几乎不会死亡，主要关注探索和解谜
    - 普通难度：偶尔有危险，但给玩家足够的逃生机会
    - 困难难度：有一定挑战性，需要谨慎选择
    - 地狱难度：高风险高回报，但仍然要给玩家生存的希望
30. **安全期机制**：故事的前3章为安全期，不会因意外或错误选择触发死亡，给玩家适应故事的时间
31. **结局合理性**：结局应该与玩家的选择序列相匹配，避免突兀的结局。死亡结局必须有充分的铺垫和合理的因果关系

**输出格式示例：**
正确的输出应该是：
```
你握紧手中的宝剑，小心翼翼地踏入黑暗的山洞。潮湿的空气中弥漫着硫磺的味道，远处传来低沉的咆哮声。突然，前方出现了三条岔路：左边的通道闪烁着微弱的蓝光，中间的通道传来水滴声，右边的通道则一片死寂。
```

**错误示例（禁止这样输出）：**
```
### 第三章：山洞探险
王子来到了山洞...

---
请做出你的选择：
1. ...
```

请直接开始讲述故事，不要有任何开场白或结束语。
"""

# 定义网文小说的系统提示
NOVEL_PROMPT = """
你是一位专业的网络小说作家，擅长创作引人入胜、扣人心弦的小说内容。

**核心写作原则：**
1. **强烈的代入感**：让读者能够身临其境，感受角色的情感和处境
2. **悬念设置**：每章结尾都要留下悬念或伏笔，让读者有强烈的继续阅读欲望
3. **节奏把控**：张弛有度，既有紧张刺激的情节，也有适当的铺垫和情感描写
4. **人物塑造**：角色性格鲜明，行为动机合理，让读者产生共鸣
5. **细节描写**：通过环境、动作、心理等细节增强画面感
6. **冲突设计**：制造合理的矛盾冲突，推动剧情发展
7. **反转惊喜**：适时安排出人意料的转折，保持新鲜感
8. **情感渲染**：通过细腻的情感描写打动读者

**写作技巧要求：**
- 开篇要抓人眼球，快速建立情境和冲突
- 对话要符合人物性格，推动剧情或展现关系
- 动作场面要紧凑有力，营造紧张氛围
- 情感戏要真挚动人，避免矫揉造作
- 世界观设定要自然融入叙事，不生硬堆砌
- 每章控制在800-1500字左右，保证阅读体验
- 语言流畅生动，避免冗长枯燥的描述
- 适当使用修辞手法增强表现力
- 保持前后逻辑一致，伏笔要有呼应
- 章节结尾要留有钩子（悬念、危机、新发现等）

**禁止事项：**
- 不要写章节标题（如"第一章"、"XX篇"等）
- 不要添加作者注释或说明性文字
- 不要一次性写完整个故事，要留有余地
- 不要偏离用户设定的题材和风格
- 不要出现逻辑矛盾或人物崩坏
- 不要过度使用套路化表达
- 不要写与主线无关的冗余内容
- 不要在正文中添加【】等特殊标记（除非是角色对话）

**输出格式：**
直接输出小说正文内容，不需要任何前缀、后缀或格式标记。
只包含纯粹的故事情节，让读者完全沉浸在故事中。

**记住：**
你的目标是让读者欲罢不能，每一章都让他们迫不及待地想点击"下一章"！
"""

# 定义漫画脚本的系统提示
COMIC_PROMPT = """
你是一位专业的黑白日式漫画（Manga）分镜师，精通日本漫画的构图语言和视觉叙事技法。你的任务是将故事章节转化为一幅具有强烈黑白漫画风格的核心画面。

## 一、黑白日漫画风核心要求

**黑白单色美学：**
- 全部画面为黑白单色，不使用彩色描述
- 用纯黑涂黑、深灰、浅灰、留白四个层次构建画面
- 大面积纯黑涂黑区域用于阴影、剪影、氛围营造
- 白色区域作为高光和呼吸空间，黑与白的面积比例约6:4到7:3

**线条与笔触：**
- 主轮廓线粗黑有力（G笔尖风格），内部细节线细腻柔韧（圆笔尖风格）
- 发丝、衣褶用细密排线表现质感和体积
- 阴影部分用斜向平行排线或交叉排线，不用平滑渐变
- 速度线、集中线、闪光效果线用于强化动态和情绪

**网点纸效果：**
- 灰度区域使用网点纸纹理，而非平滑灰度渐变
- 天空、阴影、衣物纹理用不同密度的网点区分层次
- 背景可用渐层网点增加深度
- 高光部分用刮网技法提亮

**日漫特有视觉符号：**
- 汗滴表示紧张或尴尬，青筋符号表示愤怒
- 情绪背景：开心时用花卉/星光集中线，震惊时用放射状速度线，低落时用纵向排线
- 对话框造型服务于情绪：尖叫用锯齿刺刺框，内心独白用云朵框，正常对话用椭圆框

## 二、剧情贴合原则

**关键瞬间选择：**
- 必须选择本章情节的「决定性画面」——最具戏剧冲击力或情感张力的那一瞬间
- 这个画面要能单独讲述本章的核心故事：让读者只看这一格就能感受到发生了什么
- 优先选择：角色做出关键抉择的时刻、战斗的决胜一击、情感爆发的顶点、真相揭晓的刹那

**剧情与视觉的一致性：**
- 人物表情和动作必须精确反映该章节的情节发展和角色内心状态
- 环境氛围要服务于故事情绪：危机四伏用暗黑剪影+密集斜线，平静时刻用留白+轻柔排线
- 道具和细节要呼应前文伏笔或本章关键物件，不能无意义堆砌

**跨章节连贯：**
- 角色外貌特征（发型、服饰、体型、标志性物件）保持前后一致
- 如果前章出现过特定场景/道具，本章画面中应合理延续或呼应
- 故事基调决定画面基调：热血战斗用大面积速度线和黑色块，悬疑推理用高对比光影和留白

## 三、分镜构图要求

**画面类型（shot_type）选择指南：**
- 「胸上特写」：情感对峙、内心独白、关键台词时刻
- 「脸部大特写」：震惊、决心、愤怒、悲伤等极致情绪
- 「远景」：世界观展示、旅途、孤独感、场景转换
- 「中景」：战斗动作、多人互动、对话场景
- 「鸟瞰」：绝境、渺小感、全局观察
- 「仰视」：威严、压迫感、敌人登场、气势对决

**画面描述（description）必须包含：**
1. 构图：画面中角色的位置、大小比例、与背景的空间关系
2. 主体：角色的具体动作姿势（动态线）、表情细节（眉、眼、嘴的形态）、视线方向
3. 背景：场景环境的具体细节、透视关系、景深处理
4. 黑白处理：明确指出画面的黑色块位置、排线区域、网点区域、留白区域
5. 特殊效果：速度线方向、集中线焦点、光效位置
6. 氛围：画面整体的情绪基调（紧张/悲伤/激昂/宁静等）

**画面描述格式要求：**
请提供两个版本的画面描述：
1. description: 一段完整流畅的英文描述，用于AI图片生成
2. description_cn: 对应的中文描述，用于前端展示给用户

英文描述需要包含上述所有元素，使用具体、可感的视觉词汇。
中文描述应该准确翻译英文描述的内容，保持相同的细节和视觉效果。

## 四、输出格式

以JSON格式输出，结构如下：
{
  "chapter": 章节号,
  "title": "本章标题（中文标题，格式如『决意之晨』『最后的抉择』）",
  "emotional_tone": "本章画面的情感基调（如：紧张、热血、悲伤、温馨、绝望、悲壮、激昂、宁静等）",
  "panel": {
    "shot_type": "胸上特写 / 脸部大特写 / 远景 / 中景 / 鸟瞰 / 仰视",
    "angle": "平视 / 俯视 / 仰视 / 斜角 / 鸟瞰",
    "description": "详细的黑白日漫画面描述（英文），包含构图、角色、表情、动作、背景、黑白处理、网点、速度线等所有视觉元素，用于AI图片生成",
    "description_cn": "详细的黑白日漫画面描述（中文），与description对应，用于前端展示给用户",
    "manga_techniques": "本章画面使用的日漫核心技法（如：大面积涂黑、斜向平行排线、网点纸纹理、速度线、集中线、渐层网点、刮网高光等）",
    "dialogue": "角色对白（中文，置于对话框内）",
    "inner_monologue": "角色内心独白（中文，如有，用云朵框包裹）",
    "sfx": "漫画拟声词（中文，如：轰隆！、哗啦——、咚咚…、呼——等手写体拟声词）",
    "narrative_caption": "旁白/叙事框文字（中文，用于交代时间地点或氛围）"
  }
}

## 五、实例参考

以下是一个优秀的黑白日漫画面描述示例：

{
  "chapter": 7,
  "title": "『最后的抉择』",
  "emotional_tone": "悲壮、决绝",
  "panel": {
    "shot_type": "仰视",
    "angle": "仰视",
    "description": "A low-angle close-up shot of a young swordsman standing on a rain-soaked cliff edge. The composition places him at center frame, looking up toward a darkened sky with dense diagonal rain streaks (speed lines). His face is half-lit from below by a dramatic rim light, the other half swallowed in heavy black ink shadow. His eyes show fierce determination mixed with sorrow — brows furrowed, lips pressed tight. His katana is held diagonally across his body, blade catching a sharp white highlight. His coat billows violently in the wind, rendered with bold calligraphic strokes. Background: storm clouds rendered with dense cross-hatching, rain depicted as sharp white slashing lines against a dark gray sky. Screen tone gradation from dark gray at top to mid-gray at horizon. Light rays burst from behind his silhouette. Black ink pools swallow the lower third of the frame, suggesting the abyss below.",
    "description_cn": "低角度特写镜头，一位年轻剑士站在被雨水浸湿的悬崖边缘。构图将他置于画面中央，他抬头望向黑暗的天空，天空中有密集的斜向雨丝（速度线）。他的脸被下方的戏剧性轮廓光照亮一半，另一半则被浓重的黑色墨水阴影吞噬。他的眼睛显示出坚定的决心和悲伤——眉头紧锁，嘴唇紧闭。他的武士刀斜握在身体上，刀刃捕捉到锐利的白色高光。他的外套在风中剧烈飘扬，用大胆的书法笔触渲染。背景：用密集交叉排线渲染的暴风云，雨被描绘成对抗深灰色天空的锐利白色切割线。屏幕色调从顶部的深灰色渐变到地平线的中灰色。光线从他身后爆发。黑色墨水池吞没了画面的下三分之一，暗示着下方的深渊。",
    "manga_techniques": "大面积涂黑（深渊与暗部）、斜向平行排线（云层纹理）、速度线（雨丝动态）、集中线（逆光放射效果）、渐层网点（天空层次过渡）",
    "dialogue": "…我好像，已经没有退路了。",
    "inner_monologue": "如果这就是结局……至少，是我自己选的。",
    "sfx": "哗哗哗……（雨声）轰隆隆……（远处雷鸣）",
    "narrative_caption": "第七章 —— 风暴将至，无人能逃。"
  }
}

## 六、禁止事项

- 禁止使用彩色描述（如"蓝色天空""金色阳光""红色血液"），一律转化为黑白对比描述
- 禁止含糊概括（如"画面很震撼"），必须给出具体的视觉元素
- 禁止脱离剧情随意创作画面，必须严格基于本章情节
- 禁止description字段使用中文，必须使用英文（因为需要输入给AI图片生成模型）
- description_cn字段必须使用中文，用于前端展示
- 禁止在shot_type、manga_techniques、dialogue、inner_monologue、sfx、narrative_caption、title等前端展示字段中使用日文，必须全部使用中文
- 禁止画面中无意义的装饰元素，每个视觉元素都应服务于剧情和氛围
"""


def initialize_story():
    """初始化故事状态"""
    return {
        "chapter": 1,
        "choices_made": [],
        "story_history": [],
        "story_summary": "",
        "summary_update_interval": 5,
        "inventory": [],
        "story_background": "",
        "ending_type": None,
        "custom_action_pending": False
    }


def initialize_novel(config: Dict = None):
    """初始化小说状态"""
    if config is None:
        config = {}

    return {
        "current_chapter": 1,
        "total_chapters": config.get("total_chapters", 0),
        "novel_config": config,
        "chapters_content": {},
        "novel_summary": "",
        "characters": [],
        "plot_points": [],
        "is_completed": False
    }


def initialize_comic(config: Dict = None):
    """初始化漫画状态"""
    if config is None:
        config = {}

    return {
        "current_chapter": 1,
        "total_chapters": config.get("total_chapters", 0),
        "comic_config": config,
        "chapters_content": {},
        "is_completed": False
    }


# 全局存储 agent 实例，避免重复创建导致记忆丢失
story_agents = {}
novel_agents = {}
comic_agents = {}


def create_story_agent(thread_id: str):
    """创建故事智能体"""
    if thread_id not in story_agents:
        checkpointer = InMemorySaver()
        agent = create_agent(
            model=model,
            tools=[],
            system_prompt=STORY_PROMPT,
            checkpointer=checkpointer
        )
        story_agents[thread_id] = agent
    return story_agents[thread_id]


def create_novel_agent(thread_id: str):
    """创建网文小说智能体"""
    if thread_id not in novel_agents:
        checkpointer = InMemorySaver()
        agent = create_agent(
            model=model,
            tools=[],
            system_prompt=NOVEL_PROMPT,
            checkpointer=checkpointer
        )
        novel_agents[thread_id] = agent
    return novel_agents[thread_id]


def create_comic_agent(thread_id: str):
    """创建漫画智能体"""
    if thread_id not in comic_agents:
        # 检查qwen_model是否可用
        if qwen_model is None:
            raise Exception("漫画功能需要设置 DASHSCOPE_API_KEY 环境变量")
        
        checkpointer = InMemorySaver()
        agent = create_agent(
            model=qwen_model,
            tools=[],
            system_prompt=COMIC_PROMPT,
            checkpointer=checkpointer
        )
        comic_agents[thread_id] = agent
    return comic_agents[thread_id]


def generate_story_segment(agent, user_choice: str = None, thread_id: str = "default",
                           story_background: str = "") -> str:
    """生成故事片段"""
    config = {"configurable": {"thread_id": thread_id}}

    if user_choice:
        # 强化用户选择的提示，确保AI理解
        user_message = HumanMessage(content=f"""我做出了选择：{user_choice}

请根据我的选择继续推进故事。记住：
1. 必须基于我的选择来发展情节
2. 不要忽略或改变我的选择
3. 保持故事连贯性
4. 生成下一段情节和新的选项""")
    else:
        if story_background:
            initial_prompt = f"""开始故事。以下是故事背景设定：
{story_background}

请根据这个背景开始讲述故事，介绍背景并给出第一个场景的3个选项。
记住：只需要输出故事内容和选项，不要有任何额外的说明文字。"""
        else:
            initial_prompt = "开始故事，请介绍背景并给出第一个场景的3个选项。只需要输出故事内容和选项。"
        user_message = HumanMessage(content=initial_prompt)

    response_chunks = []
    try:
        for event in agent.stream({"messages": [user_message]}, config=config):
            if 'model' in event and 'messages' in event['model']:
                for msg in event['model']['messages']:
                    if hasattr(msg, 'content') and msg.content:
                        response_chunks.append(msg.content)
            elif 'messages' in event:
                for msg in event['messages']:
                    if hasattr(msg, 'content') and msg.content:
                        response_chunks.append(msg.content)
            elif 'agent' in event and 'messages' in event['agent']:
                for msg in event['agent']['messages']:
                    if hasattr(msg, 'content') and msg.content:
                        response_chunks.append(msg.content)
    except Exception as e:
        print(f"生成故事时出错: {e}")
        raise

    full_response = "".join(response_chunks)
    
    # 验证响应是否包含必要的内容
    if not full_response or len(full_response.strip()) < 10:
        raise Exception("AI返回的内容过短或为空")
    
    return full_response


def generate_novel_chapter(agent, chapter_num: int, novel_config: Dict, previous_chapters: str = "", thread_id: str = "default") -> str:
    """生成网文章节"""
    config = {"configurable": {"thread_id": thread_id}}

    genre = novel_config.get("genre", "玄幻")
    style = novel_config.get("style", "热血")
    total_chapters = novel_config.get("total_chapters", 0)
    custom_intro = novel_config.get("custom_intro", "")

    if total_chapters > 0:
        chapter_info = f"这是第{chapter_num}章，总共{total_chapters}章"
    else:
        chapter_info = f"这是第{chapter_num}章（无限连载模式）"

    # 如果有前文摘要，加入提示
    context_hint = ""
    if previous_chapters:
        # 增加摘要长度到500字，提供更多上下文
        context_hint = f"""
前情提要（最近章节内容摘要）：
{previous_chapters}

请确保本章内容与前面章节连贯，保持人物性格、剧情发展和世界观的一致性。"""

    prompt_content = f"""请创作{genre}题材、{style}风格的网络小说。
{chapter_info}。
{f'故事背景：{custom_intro}' if custom_intro else ''}
{context_hint}

请确保：
1. 内容与之前章节连贯，保持人物性格和剧情一致性
2. 本章要有足够的吸引力，让读者想继续阅读下一章
3. 章节结尾留下悬念或伏笔
4. 字数控制在800-1500字左右
5. 直接输出小说正文，不要有任何标题、说明或标记
6. 如果这是第一章，需要建立世界观和引入主角
7. 如果是后续章节，要承接上文并推动剧情发展"""

    user_message = HumanMessage(content=prompt_content)

    response_chunks = []
    try:
        for event in agent.stream({"messages": [user_message]}, config=config):
            if 'model' in event and 'messages' in event['model']:
                for msg in event['model']['messages']:
                    if hasattr(msg, 'content') and msg.content:
                        response_chunks.append(msg.content)
            elif 'messages' in event:
                for msg in event['messages']:
                    if hasattr(msg, 'content') and msg.content:
                        response_chunks.append(msg.content)
            elif 'agent' in event and 'messages' in event['agent']:
                for msg in event['agent']['messages']:
                    if hasattr(msg, 'content') and msg.content:
                        response_chunks.append(msg.content)
    except Exception as e:
        print(f"生成小说章节时出错: {e}")
        raise

    full_response = "".join(response_chunks)
    
    # 验证响应
    if not full_response or len(full_response.strip()) < 100:
        raise Exception("AI返回的内容过短或为空，请重试")
    
    return full_response


def generate_panel_image(description: str, style: str = "anime") -> str:
    """使用DashScope文生图API生成单个分镜图片"""
    if not DASHSCOPE_AVAILABLE:
        print("❌ dashscope 库未安装，无法生成图片")
        return ""

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("❌ DASHSCOPE_API_KEY 环境变量未设置，无法生成图片")
        return ""

    try:
        # 构建文生图提示词（去除多余缩进）
        prompt = (
            f"{description}\n\n"
            "Style: black and white Japanese manga style, monochrome ink drawing, "
            "screen tone texture, bold lineart, high contrast, no color. "
            "Quality: Masterpiece, best quality, ultra-detailed, sharp lines."
        )
        negative_prompt = (
            "color, pastel, watercolor, grainy, blurry, low contrast, 3D render, "
            "photorealistic, cgi, digital painting"
        )

        print(f"🎨 正在调用 DashScope 文生图 API...")
        print(f"   Prompt 长度: {len(prompt)} 字符")

        # 确保 dashscope 能读取到 API key（兼容不同版本）
        import dashscope
        dashscope.api_key = api_key

        response = ImageSynthesis.call(
            model='wanx2.1-t2i-turbo',
            prompt=prompt,
            negative_prompt=negative_prompt,
            size='1024*1024',
            n=1,
            api_key=api_key
        )

        print(f"   API 响应状态码: {response.status_code}")

        if response.status_code == 200 and response.output:
            if hasattr(response.output, 'results') and response.output.results:
                url = response.output.results[0].url
                print(f"✅ 图片生成成功: {url[:80]}...")
                return url
            else:
                print(f"❌ API 返回成功但无 results: {response.output}")
        else:
            print(f"❌ API 调用失败: status_code={response.status_code}")
            if hasattr(response, 'message'):
                print(f"   错误信息: {response.message}")
            if hasattr(response, 'code'):
                print(f"   错误码: {response.code}")

        return ""
    except Exception as e:
        print(f"❌ 生成图片异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return ""


def generate_comic_images(chapter_data: Dict, style: str = "anime") -> Dict:
    """为整个章节生成单张图片"""
    panel = chapter_data.get('panel', {})

    description = panel.get('description', '')
    if not description:
        print(f"⚠️ 第{chapter_data.get('chapter')}章没有画面描述，跳过图片生成")
        panel['image_url'] = ""
        panel['image_error'] = "缺少画面描述"
        return chapter_data

    print(f"正在生成第{chapter_data.get('chapter')}章的图片...")
    image_url = generate_panel_image(description, style)
    if image_url:
        panel['image_url'] = image_url
        panel['image_error'] = ""
        print(f"✅ 第{chapter_data.get('chapter')}章图片生成成功")
    else:
        panel['image_url'] = ""
        panel['image_error'] = "图片生成失败，请检查服务端日志"
        print(f"❌ 第{chapter_data.get('chapter')}章图片生成失败")

    return chapter_data


def generate_comic_chapter(agent, chapter_num: int, comic_config: Dict, previous_chapters_summary: str = "", thread_id: str = "default", generate_images: bool = False) -> Dict:
    """生成漫画章节（分镜脚本）"""
    config = {"configurable": {"thread_id": thread_id}}

    genre = comic_config.get("genre", "奇幻")
    style = comic_config.get("style", "热血")
    total_chapters = comic_config.get("total_chapters", 0)
    custom_intro = comic_config.get("custom_intro", "")

    if total_chapters > 0:
        chapter_info = f"这是第{chapter_num}章，总共{total_chapters}章"
    else:
        chapter_info = f"这是第{chapter_num}章（无限连载模式）"

    # 如果有前文摘要，加入提示
    context_hint = ""
    if previous_chapters_summary:
        context_hint = f"""
前情提要：
{previous_chapters_summary}

请确保本章内容与前面章节连贯，保持角色形象和剧情发展的一致性。"""

    prompt_content = f"""请以黑白日式漫画（Manga）风格创作单幅核心画面。
{chapter_info}。
{f'故事背景：{custom_intro}' if custom_intro else ''}
{context_hint}

请严格遵循你的系统提示，确保：
1. 选择本章最关键的「决定性瞬间」，让画面本身就能讲述本章核心故事
2. 画面描述(description)必须用英文撰写（用于AI图片生成），包含完整的黑白漫画视觉元素
3. 明确标注使用的日漫技法（大面积涂黑、斜向平行排线、网点纸纹理、速度线、集中线等）
4. 人物表情和动作必须精确反映本章的情节发展和角色内心状态
5. 以JSON格式输出，所有字段不可省略，所有展示文本字段必须使用中文
6. 首章需建立世界观和引入主角，后续章节必须承接上文"""

    user_message = HumanMessage(content=prompt_content)

    response_chunks = []
    try:
        for event in agent.stream({"messages": [user_message]}, config=config):
            if 'model' in event and 'messages' in event['model']:
                for msg in event['model']['messages']:
                    if hasattr(msg, 'content') and msg.content:
                        response_chunks.append(msg.content)
            elif 'messages' in event:
                for msg in event['messages']:
                    if hasattr(msg, 'content') and msg.content:
                        response_chunks.append(msg.content)
            elif 'agent' in event and 'messages' in event['agent']:
                for msg in event['agent']['messages']:
                    if hasattr(msg, 'content') and msg.content:
                        response_chunks.append(msg.content)
    except Exception as e:
        print(f"生成漫画章节时出错: {e}")
        raise

    full_response = "".join(response_chunks)
    
    # 尝试解析JSON
    try:
        # 提取JSON部分（可能包含在代码块中）
        json_match = re.search(r'```json\s*([\s\S]*?)```', full_response)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接解析
            json_str = full_response
        
        # 使用json.loads而不是eval，更安全
        comic_data = json.loads(json_str)
        
        # 验证基本结构 - 现在使用单个panel而不是panels数组
        if 'panel' not in comic_data or not isinstance(comic_data['panel'], dict):
            raise Exception("漫画数据结构不完整，缺少panel字段")
        
        # 验证panel的必要字段
        panel = comic_data['panel']
        required_fields = ['shot_type', 'angle', 'description', 'description_cn']
        for field in required_fields:
            if field not in panel:
                raise Exception(f"panel缺少必要字段: {field}")
        
        # 如果需要生成图片，调用图片生成函数（现在默认不生成，由前端异步请求）
        if generate_images:
            print("\n开始为章节生成图片...")
            comic_data = generate_comic_images(comic_data, style)
            print("图片生成完成！\n")
        
        return comic_data
    except Exception as e:
        print(f"解析漫画JSON失败: {e}")
        print(f"原始响应: {full_response[:500]}")
        raise Exception(f"漫画数据解析失败: {str(e)}")


def parse_options(text: str) -> List[str]:
    """从文本中解析选项"""
    # 模式1: 【选项1】... 【选项2】... 【选项3】... 【选项4】...
    options = re.findall(r'【选项\d+】([^【]+)', text)

    # 模式2: 选项1:... 选项2:... 选项3:... 选项4:...
    if not options or len(options) < 3:
        options = re.findall(r'选项\d+[:：]\s*([^选项]+?)(?=选项\d+|$)', text)

    # 模式3: 1. ... 2. ... 3. ... 4. ...
    if not options or len(options) < 3:
        options = re.findall(r'\d+\.\s*([^\d]+?)(?=\d+\.|$)', text)

    cleaned_options = []
    for opt in options:
        opt = opt.strip()
        if len(opt) > 50:
            opt = opt[:50] + "..."
        if opt:
            cleaned_options.append(opt)

    if len(cleaned_options) < 3:
        return []

    if len(cleaned_options) >= 4:
        if "自定义" not in cleaned_options[3] and "自行" not in cleaned_options[3]:
            cleaned_options[3] = "自定义行动"
    elif len(cleaned_options) == 3:
        cleaned_options.append("自定义行动")

    return cleaned_options[:4]


def extract_story_content(text: str) -> str:
    """从AI响应中提取纯故事内容"""
    cleaned_text = re.sub(r'【选项\d+】[^【]*', '', text)
    cleaned_text = re.sub(r'选项\d+[:：][^选项]*', '', cleaned_text)
    cleaned_text = re.sub(r'【结局:(成功|失败|特殊|坏结局)】', '', cleaned_text)
    cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)
    return cleaned_text.strip()


def check_ending(text: str) -> str:
    """检查文本中是否包含结局标记"""
    if re.search(r'【结局:成功】', text):
        return "success"
    elif re.search(r'【结局:坏结局】', text):
        return "bad"
    elif re.search(r'【结局:失败】', text):
        return "failure"
    elif re.search(r'【结局:特殊】', text):
        return "special"
    else:
        return None


# ==================== Flask 路由 ====================

@app.route('/')
def index():
    """主页"""
    return render_template('web.html')


@app.route('/api/story/start', methods=['POST'])
def start_story():
    """开始新的互动故事"""
    import time
    start_time = time.time()
    print(f"\n{'='*50}")
    print(f"开始生成互动故事...")
    
    data = request.get_json(silent=True) or {}
    theme = data.get('theme', '奇幻冒险')
    background = data.get('background', '')
    difficulty = data.get('difficulty', '普通')
    
    print(f"主题: {theme}, 难度: {difficulty}")
    if background:
        print(f"背景: {background[:100]}...")

    # 生成唯一的 thread_id
    thread_id = str(uuid.uuid4())
    
    # 初始化故事状态
    story_state = initialize_story()
    background_info = f"故事主题：{theme}，难度：{difficulty}"
    if background:
        background_info += f"\n背景设定：{background}"
    story_state['story_background'] = background_info

    # 保存到 session
    session['story_thread_id'] = thread_id
    session['story_state'] = story_state

    # 创建 agent 并生成第一段故事
    print("正在初始化AI智能体...")
    agent = create_story_agent(thread_id)
    try:
        print("正在生成故事内容...")
        full_text = generate_story_segment(agent, None, thread_id, background_info)
        
        elapsed = time.time() - start_time
        print(f"故事生成完成！耗时: {elapsed:.2f}秒")
        print(f"{'='*50}\n")
        
        story_content = extract_story_content(full_text)
        options = parse_options(full_text)
        ending_type = check_ending(full_text)

        # 更新状态
        story_state['story_history'].append(story_content)
        session['story_state'] = story_state

        return jsonify({
            'success': True,
            'content': story_content,
            'options': options,
            'chapter': story_state['chapter'],
            'game_over': ending_type is not None,
            'ending_type': ending_type,
            'generation_time': round(elapsed, 2)  # 返回生成时间
        })
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"生成失败！耗时: {elapsed:.2f}秒, 错误: {str(e)}")
        print(f"{'='*50}\n")
        return jsonify({'success': False, 'error': f'生成故事失败: {str(e)}'}), 500


@app.route('/api/story/choose', methods=['POST'])
def story_choose():
    """用户做出选择"""
    import time
    start_time = time.time()
    
    data = request.get_json(silent=True) or {}
    choice = data.get('choice', '')
    
    print(f"\n用户选择: {choice}")

    thread_id = session.get('story_thread_id')
    story_state = session.get('story_state')

    if not thread_id or not story_state:
        return jsonify({'success': False, 'error': '故事未初始化'}), 400

    # 检查是否已经游戏结束，如果是则不允许继续
    if story_state.get('ending_type') is not None:
        return jsonify({
            'success': True,
            'content': story_state['story_history'][-1] if story_state['story_history'] else '故事已结束',
            'options': [],
            'chapter': story_state['chapter'],
            'game_over': True,
            'ending_type': story_state['ending_type']
        })

    # 记录选择
    story_state['choices_made'].append(choice)
    story_state['chapter'] += 1

    # 创建 agent 并生成下一段故事
    agent = create_story_agent(thread_id)
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"正在生成第{story_state['chapter']}章 (尝试 {attempt + 1}/{max_retries})...")
            full_text = generate_story_segment(agent, choice, thread_id, story_state.get('story_background', ''))
            
            elapsed = time.time() - start_time
            print(f"第{story_state['chapter']}章生成完成！耗时: {elapsed:.2f}秒")
            
            story_content = extract_story_content(full_text)
            ending_type = check_ending(full_text)
            
            # 如果触发了结局，不再解析选项
            if ending_type:
                print(f"检测到结局类型: {ending_type}")
                options = []
            else:
                options = parse_options(full_text)
                # 验证选项是否有效
                if not options or len(options) < 3:
                    if attempt < max_retries - 1:
                        print(f"第{attempt + 1}次尝试失败：选项解析失败，重试...")
                        continue
                    else:
                        # 如果最后一次也失败了，使用默认选项
                        options = ["继续探索", "返回原地", "仔细观察四周", "自定义行动"]

            # 更新状态
            story_state['story_history'].append(story_content)
            story_state['ending_type'] = ending_type  # 保存结局类型到状态
            session['story_state'] = story_state

            return jsonify({
                'success': True,
                'content': story_content,
                'options': options,
                'chapter': story_state['chapter'],
                'game_over': ending_type is not None,
                'ending_type': ending_type,
                'generation_time': round(elapsed, 2)  # 返回生成时间
            })
        except Exception as e:
            print(f"第{attempt + 1}次尝试出错: {str(e)}")
            if attempt >= max_retries - 1:
                elapsed = time.time() - start_time
                print(f"生成失败！总耗时: {elapsed:.2f}秒")
                return jsonify({'success': False, 'error': f'生成故事失败: {str(e)}'}), 500


@app.route('/api/story/reset', methods=['POST'])
def reset_story():
    """重置故事"""
    session.pop('story_thread_id', None)
    session.pop('story_state', None)
    return jsonify({'success': True})


@app.route('/api/novel/start', methods=['POST'])
def start_novel():
    """开始新的网文小说"""
    import time
    start_time = time.time()
    print(f"\n{'='*50}")
    print(f"开始生成网文小说第一章...")
    
    data = request.get_json(silent=True) or {}
    genre = data.get('genre', '玄幻')
    style = data.get('style', '热血')
    total_chapters = int(data.get('total_chapters', 0))
    custom_intro = data.get('custom_intro', '')

    print(f"题材: {genre}, 风格: {style}")
    if total_chapters > 0:
        print(f"总章数: {total_chapters}")
    else:
        print(f"模式: 无限连载")
    if custom_intro:
        print(f"简介: {custom_intro[:100]}...")

    # 生成唯一的 thread_id
    thread_id = str(uuid.uuid4())

    # 初始化小说状态
    novel_config = {
        "genre": genre,
        "style": style,
        "total_chapters": total_chapters,
        "custom_intro": custom_intro
    }
    novel_state = initialize_novel(novel_config)

    # 保存到 session
    session['novel_thread_id'] = thread_id
    session['novel_state'] = novel_state

    # 创建 agent 并生成第一章
    print("正在初始化AI作家...")
    agent = create_novel_agent(thread_id)
    
    max_retries = 2
    for attempt in range(max_retries):
        try:
            print(f"正在创作第一章 (尝试 {attempt + 1}/{max_retries})...")
            chapter_content = generate_novel_chapter(agent, 1, novel_config, "", thread_id)
            
            if not chapter_content or len(chapter_content.strip()) == 0:
                if attempt < max_retries - 1:
                    print(f"第{attempt + 1}次尝试失败：内容为空，重试...")
                    continue
                else:
                    elapsed = time.time() - start_time
                    print(f"生成失败！耗时: {elapsed:.2f}秒")
                    print(f"{'='*50}\n")
                    return jsonify({'success': False, 'error': 'AI未返回有效内容，请重试'}), 500

            elapsed = time.time() - start_time
            print(f"第一章创作完成！耗时: {elapsed:.2f}秒, 字数: {len(chapter_content)}")
            print(f"{'='*50}\n")

            # 更新状态
            novel_state['current_chapter'] = 1
            novel_state['chapters_content'][1] = chapter_content
            session['novel_state'] = novel_state
            session.modified = True  # 强制标记session已修改
            
            print(f"小说状态已保存到session")
            print(f"thread_id: {thread_id}")
            print(f"current_chapter: {novel_state['current_chapter']}")
            print(f"chapters_content keys: {list(novel_state['chapters_content'].keys())}")
            print(f"Session keys after save: {list(session.keys())}")

            return jsonify({
                'success': True,
                'content': chapter_content,
                'chapter': 1,
                'total_chapters': total_chapters,
                'is_completed': False,
                'genre': genre,
                'style': style
            })
        except Exception as e:
            print(f"第{attempt + 1}次尝试出错: {str(e)}")
            if attempt >= max_retries - 1:
                elapsed = time.time() - start_time
                print(f"生成失败！耗时: {elapsed:.2f}秒")
                print(f"{'='*50}\n")
                return jsonify({'success': False, 'error': f'生成失败: {str(e)}'}), 500


@app.route('/api/novel/next', methods=['POST'])
def next_chapter():
    """生成下一章"""
    import time
    start_time = time.time()
    print(f"\n{'='*50}")
    print(f"请求生成下一章")
    
    # 详细调试信息
    print(f"Session keys: {list(session.keys())}")
    print(f"Session size estimate: {len(str(session))} bytes")
    
    thread_id = session.get('novel_thread_id')
    novel_state = session.get('novel_state')
    
    print(f"thread_id: {thread_id}")
    print(f"novel_state exists: {novel_state is not None}")
    if novel_state:
        print(f"current_chapter: {novel_state.get('current_chapter')}")
        print(f"chapters_content keys: {list(novel_state.get('chapters_content', {}).keys())}")
        print(f"novel_config: {novel_state.get('novel_config', {})}")
        print(f"is_completed: {novel_state.get('is_completed')}")

    if not thread_id or not novel_state:
        print(f"❌ 错误：小说未初始化！")
        print(f"{'='*50}\n")
        return jsonify({'success': False, 'error': '小说未初始化，请重新开始'}), 400

    next_chapter_num = novel_state['current_chapter'] + 1
    config = novel_state['novel_config']

    print(f"目标章节: 第{next_chapter_num}章")
    print(f"总章数设置: {config.get('total_chapters', 0)}")

    # 检查是否已完结
    if config.get('total_chapters', 0) > 0 and next_chapter_num > config.get('total_chapters', 0):
        print(f"✅ 小说已完结（达到总章数{config.get('total_chapters', 0)}）")
        return jsonify({'success': True, 'is_completed': True})

    # 创建 agent 并生成下一章
    agent = create_novel_agent(thread_id)
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"\n正在创作第{next_chapter_num}章 (尝试 {attempt + 1}/{max_retries})...")
            
            # 获取前面章节的内容作为上下文（最多3章，每章800字）
            previous_summary = ""
            chapters_to_include = []
            
            # 收集前面最多3章的内容
            start_chapter = max(1, next_chapter_num - 3)
            print(f"需要加载前文章节范围: {start_chapter} - {next_chapter_num - 1}")
            
            for i in range(start_chapter, next_chapter_num):
                if i in novel_state['chapters_content']:
                    chapter_text = novel_state['chapters_content'][i]
                    # 每章取前800字，提供更多上下文
                    chapters_to_include.append(f"第{i}章摘要：{chapter_text[:800]}...")
                    print(f"  ✅ 已加载第{i}章 ({len(chapter_text)}字)")
                else:
                    print(f"  ❌ 第{i}章不存在于缓存中")
            
            if chapters_to_include:
                previous_summary = "\n\n".join(chapters_to_include)
                print(f"✅ 使用前文摘要，包含 {len(chapters_to_include)} 章内容")
            else:
                print(f"️  警告：没有找到前文内容！")
            
            chapter_content = generate_novel_chapter(
                agent, 
                next_chapter_num, 
                config, 
                previous_summary,
                thread_id
            )
            
            # 验证内容质量
            content_length = len(chapter_content.strip()) if chapter_content else 0
            print(f"生成内容长度: {content_length}字")
            
            if not chapter_content or content_length < 200:
                if attempt < max_retries - 1:
                    print(f" 第{attempt + 1}次尝试失败：内容过短 ({content_length}字)，重试...")
                    continue
                else:
                    elapsed = time.time() - start_time
                    print(f"❌ 生成失败！耗时: {elapsed:.2f}秒")
                    print(f"{'='*50}\n")
                    return jsonify({'success': False, 'error': 'AI未返回有效内容，请重试'}), 500

            elapsed = time.time() - start_time
            print(f"\n✅ 第{next_chapter_num}章创作完成！")
            print(f"   耗时: {elapsed:.2f}秒")
            print(f"   字数: {content_length}")
            print(f"{'='*50}\n")

            # 更新状态
            novel_state['current_chapter'] = next_chapter_num
            novel_state['chapters_content'][next_chapter_num] = chapter_content
            
            is_completed = (
                config.get('total_chapters', 0) > 0 and
                next_chapter_num >= config.get('total_chapters', 0)
            )
            novel_state['is_completed'] = is_completed

            print(f"更新小说状态:")
            print(f"  current_chapter: {novel_state['current_chapter']}")
            print(f"  chapters_content keys: {list(novel_state['chapters_content'].keys())}")
            print(f"  is_completed: {is_completed}")
            
            # 保存到 session
            session['novel_state'] = novel_state
            session.modified = True  # 强制标记session已修改
            
            print(f"✅ 状态已保存到session")

            return jsonify({
                'success': True,
                'content': chapter_content,
                'chapter': next_chapter_num,
                'total_chapters': config.get('total_chapters', 0),
                'is_completed': is_completed,
                'genre': config.get('genre', ''),
                'style': config.get('style', ''),
                'generation_time': round(elapsed, 2)
            })
        except Exception as e:
            print(f"\n❌ 第{attempt + 1}次尝试出错:")
            print(f"   错误类型: {type(e).__name__}")
            print(f"   错误信息: {str(e)}")
            import traceback
            traceback.print_exc()
            if attempt >= max_retries - 1:
                elapsed = time.time() - start_time
                print(f"\n❌ 生成失败！总耗时: {elapsed:.2f}秒")
                print(f"{'='*50}\n")
                return jsonify({'success': False, 'error': f'生成失败: {str(e)}'}), 500


@app.route('/api/novel/reset', methods=['POST'])
def reset_novel():
    """重置小说"""
    thread_id = session.get('novel_thread_id')
    if thread_id and thread_id in novel_agents:
        del novel_agents[thread_id]  # 清理 agent 实例
    session.pop('novel_thread_id', None)
    session.pop('novel_state', None)
    return jsonify({'success': True})


@app.route('/api/comic/start', methods=['POST'])
def start_comic():
    """开始新的漫画创作"""
    import time
    start_time = time.time()
    print(f"\n{'='*50}")
    print(f"开始生成漫画第一章...")
    
    data = request.get_json(silent=True) or {}
    genre = data.get('genre', '奇幻')
    style = data.get('style', '热血')
    total_chapters = int(data.get('total_chapters', 0))
    custom_intro = data.get('custom_intro', '')

    print(f"题材: {genre}, 风格: {style}")
    if total_chapters > 0:
        print(f"总章数: {total_chapters}")
    else:
        print(f"模式: 无限连载")
    if custom_intro:
        print(f"简介: {custom_intro[:100]}...")

    # 生成唯一的 thread_id
    thread_id = str(uuid.uuid4())

    # 初始化漫画状态
    comic_config = {
        "genre": genre,
        "style": style,
        "total_chapters": total_chapters,
        "custom_intro": custom_intro
    }
    comic_state = initialize_comic(comic_config)

    # 保存到 session
    session['comic_thread_id'] = thread_id
    session['comic_state'] = comic_state

    # 创建 agent 并生成第一章
    print("正在初始化AI漫画家...")
    agent = create_comic_agent(thread_id)
    
    max_retries = 2
    for attempt in range(max_retries):
        try:
            print(f"正在创作第一章 (尝试 {attempt + 1}/{max_retries})...")
            # 不生成图片，快速返回分镜脚本
            chapter_data = generate_comic_chapter(agent, 1, comic_config, "", thread_id, generate_images=False)
            
            if not chapter_data or 'panel' not in chapter_data:
                if attempt < max_retries - 1:
                    print(f"第{attempt + 1}次尝试失败：数据格式错误，重试...")
                    continue
                else:
                    elapsed = time.time() - start_time
                    print(f"生成失败！耗时: {elapsed:.2f}秒")
                    print(f"{'='*50}\n")
                    return jsonify({'success': False, 'error': 'AI未返回有效内容，请重试'}), 500

            elapsed = time.time() - start_time
            print(f"第一章创作完成！耗时: {elapsed:.2f}秒")
            print(f"💡 提示：漫画脚本已生成，可以异步生成图片")
            print(f"{'='*50}\n")

            # 更新状态
            comic_state['current_chapter'] = 1
            comic_state['chapters_content'][1] = chapter_data
            session['comic_state'] = comic_state
            session.modified = True  # 强制标记session已修改
            
            print(f"漫画状态已保存到session")
            print(f"thread_id: {thread_id}")
            print(f"current_chapter: {comic_state['current_chapter']}")
            print(f"chapters_content keys: {list(comic_state['chapters_content'].keys())}")

            return jsonify({
                'success': True,
                'content': chapter_data,
                'chapter': 1,
                'total_chapters': total_chapters,
                'is_completed': False,
                'genre': genre,
                'style': style
            })
        except Exception as e:
            print(f"第{attempt + 1}次尝试出错: {str(e)}")
            if attempt >= max_retries - 1:
                elapsed = time.time() - start_time
                print(f"生成失败！耗时: {elapsed:.2f}秒")
                print(f"{'='*50}\n")
                return jsonify({'success': False, 'error': f'生成失败: {str(e)}'}), 500


@app.route('/api/comic/next', methods=['POST'])
def next_comic_chapter():
    """生成下一章漫画"""
    import time
    start_time = time.time()
    print(f"\n{'='*50}")
    print(f"请求生成下一章漫画")
    
    # 详细调试信息
    print(f"Session keys: {list(session.keys())}")
    
    thread_id = session.get('comic_thread_id')
    comic_state = session.get('comic_state')
    
    print(f"thread_id: {thread_id}")
    print(f"comic_state exists: {comic_state is not None}")
    if comic_state:
        print(f"current_chapter: {comic_state.get('current_chapter')}")
        print(f"chapters_content keys: {list(comic_state.get('chapters_content', {}).keys())}")
        print(f"comic_config: {comic_state.get('comic_config', {})}")
        print(f"is_completed: {comic_state.get('is_completed')}")

    if not thread_id or not comic_state:
        print(f"❌ 错误：漫画未初始化！")
        print(f"{'='*50}\n")
        return jsonify({'success': False, 'error': '漫画未初始化，请重新开始'}), 400

    next_chapter_num = comic_state['current_chapter'] + 1
    config = comic_state['comic_config']

    print(f"目标章节: 第{next_chapter_num}章")
    print(f"总章数设置: {config.get('total_chapters', 0)}")

    # 检查是否已完结
    if config.get('total_chapters', 0) > 0 and next_chapter_num > config.get('total_chapters', 0):
        print(f"✅ 漫画已完结（达到总章数{config.get('total_chapters', 0)}）")
        return jsonify({'success': True, 'is_completed': True})

    # 创建 agent 并生成下一章
    agent = create_comic_agent(thread_id)
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"\n正在创作第{next_chapter_num}章 (尝试 {attempt + 1}/{max_retries})...")
            
            # 获取前面章节的内容作为上下文（最多2章摘要）
            previous_summary = ""
            chapters_to_include = []
            
            # 收集前面最多2章的内容
            start_chapter = max(1, next_chapter_num - 2)
            print(f"需要加载前文章节范围: {start_chapter} - {next_chapter_num - 1}")
            
            for i in range(start_chapter, next_chapter_num):
                if i in comic_state['chapters_content']:
                    chapter_data = comic_state['chapters_content'][i]
                    # 提取关键信息作为摘要
                    title = chapter_data.get('title', f'第{i}章')
                    panel_desc = chapter_data.get('panel', {}).get('description', '')[:200]
                    chapters_to_include.append(f"第{i}章《{title}》:\n{panel_desc}")
                    print(f"  ✅ 已加载第{i}章")
                else:
                    print(f"  ❌ 第{i}章不存在于缓存中")
            
            if chapters_to_include:
                previous_summary = "\n\n".join(chapters_to_include)
                print(f"✅ 使用前文摘要，包含 {len(chapters_to_include)} 章内容")
            else:
                print(f"️  警告：没有找到前文内容！")
            
            chapter_data = generate_comic_chapter(
                agent, 
                next_chapter_num, 
                config, 
                previous_summary,
                thread_id,
                generate_images=False  # 不生成图片，快速返回
            )
            
            # 验证内容质量
            has_panel = 'panel' in chapter_data if chapter_data else False
            print(f"是否包含panel: {has_panel}")
            
            if not chapter_data or not has_panel:
                if attempt < max_retries - 1:
                    print(f" 第{attempt + 1}次尝试失败：数据结构不完整，重试...")
                    continue
                else:
                    elapsed = time.time() - start_time
                    print(f"❌ 生成失败！耗时: {elapsed:.2f}秒")
                    print(f"{'='*50}\n")
                    return jsonify({'success': False, 'error': 'AI未返回有效内容，请重试'}), 500

            elapsed = time.time() - start_time
            print(f"\n✅ 第{next_chapter_num}章创作完成！")
            print(f"   耗时: {elapsed:.2f}秒")
            print(f"💡 提示：漫画脚本已生成，可以异步生成图片")
            print(f"{'='*50}\n")

            # 更新状态
            comic_state['current_chapter'] = next_chapter_num
            comic_state['chapters_content'][next_chapter_num] = chapter_data
            
            is_completed = (
                config.get('total_chapters', 0) > 0 and
                next_chapter_num >= config.get('total_chapters', 0)
            )
            comic_state['is_completed'] = is_completed

            print(f"更新漫画状态:")
            print(f"  current_chapter: {comic_state['current_chapter']}")
            print(f"  chapters_content keys: {list(comic_state['chapters_content'].keys())}")
            print(f"  is_completed: {is_completed}")
            
            # 保存到 session
            session['comic_state'] = comic_state
            session.modified = True  # 强制标记session已修改
            
            print(f"✅ 状态已保存到session")

            return jsonify({
                'success': True,
                'content': chapter_data,
                'chapter': next_chapter_num,
                'total_chapters': config.get('total_chapters', 0),
                'is_completed': is_completed,
                'genre': config.get('genre', ''),
                'style': config.get('style', ''),
                'generation_time': round(elapsed, 2)
            })
        except Exception as e:
            print(f"\n❌ 第{attempt + 1}次尝试出错:")
            print(f"   错误类型: {type(e).__name__}")
            print(f"   错误信息: {str(e)}")
            import traceback
            traceback.print_exc()
            if attempt >= max_retries - 1:
                elapsed = time.time() - start_time
                print(f"\n❌ 生成失败！总耗时: {elapsed:.2f}秒")
                print(f"{'='*50}\n")
                return jsonify({'success': False, 'error': f'生成失败: {str(e)}'}), 500


@app.route('/api/comic/reset', methods=['POST'])
def reset_comic():
    """重置漫画"""
    thread_id = session.get('comic_thread_id')
    if thread_id and thread_id in comic_agents:
        del comic_agents[thread_id]  # 清理 agent 实例
    session.pop('comic_thread_id', None)
    session.pop('comic_state', None)
    return jsonify({'success': True})


@app.route('/api/comic/generate_images', methods=['POST'])
def generate_comic_images_api():
    """为指定章节生成分镜图片（异步）"""
    import time
    start_time = time.time()
    
    data = request.get_json(silent=True) or {}
    chapter_num = data.get('chapter', 1)

    print(f"\n{'='*50}")
    print(f"开始为第{chapter_num}章生成分镜图片...")
    
    thread_id = session.get('comic_thread_id')
    comic_state = session.get('comic_state')
    
    if not thread_id or not comic_state:
        return jsonify({'success': False, 'error': '漫画未初始化'}), 400
    
    # 检查章节是否存在
    if chapter_num not in comic_state['chapters_content']:
        return jsonify({'success': False, 'error': f'第{chapter_num}章不存在'}), 404
    
    chapter_data = comic_state['chapters_content'][chapter_num]
    style = comic_state['comic_config'].get('style', 'anime')
    
    try:
        # 生成图片
        print(f"正在为第{chapter_num}章生成图片...")
        updated_chapter = generate_comic_images(chapter_data, style)
        
        # 更新状态
        comic_state['chapters_content'][chapter_num] = updated_chapter
        session['comic_state'] = comic_state
        session.modified = True
        
        elapsed = time.time() - start_time
        print(f"✅ 图片生成完成！耗时: {elapsed:.2f}秒")
        print(f"{'='*50}\n")
        
        return jsonify({
            'success': True,
            'content': updated_chapter,
            'generation_time': round(elapsed, 2)
        })
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ 图片生成失败！耗时: {elapsed:.2f}秒, 错误: {str(e)}")
        print(f"{'='*50}\n")
        return jsonify({'success': False, 'error': f'图片生成失败: {str(e)}'}), 500


@app.route('/api/comic/goto', methods=['POST'])
def goto_comic_chapter():
    """跳转到指定章节"""
    data = request.get_json(silent=True) or {}
    chapter_num = data.get('chapter', 1)

    thread_id = session.get('comic_thread_id')
    comic_state = session.get('comic_state')

    if not thread_id or not comic_state:
        return jsonify({'success': False, 'error': '漫画未初始化'}), 400

    # 检查章节是否存在
    if chapter_num not in comic_state['chapters_content']:
        return jsonify({'success': False, 'error': f'第{chapter_num}章不存在'}), 404

    # 更新当前章节
    comic_state['current_chapter'] = chapter_num
    session['comic_state'] = comic_state
    session.modified = True

    config = comic_state['comic_config']
    is_completed = (
        config.get('total_chapters', 0) > 0 and
        chapter_num >= config.get('total_chapters', 0)
    )
    
    return jsonify({
        'success': True,
        'content': comic_state['chapters_content'][chapter_num],
        'chapter': chapter_num,
        'total_chapters': config.get('total_chapters', 0),
        'is_completed': is_completed,
        'genre': config.get('genre', ''),
        'style': config.get('style', '')
    })


@app.route('/api/novel/goto', methods=['POST'])
def goto_chapter():
    """跳转到指定章节"""
    data = request.get_json(silent=True) or {}
    chapter_num = data.get('chapter', 1)

    thread_id = session.get('novel_thread_id')
    novel_state = session.get('novel_state')

    if not thread_id or not novel_state:
        return jsonify({'success': False, 'error': '小说未初始化'}), 400

    # 检查章节是否存在
    if chapter_num not in novel_state['chapters_content']:
        return jsonify({'success': False, 'error': f'第{chapter_num}章不存在'}), 404

    # 更新当前章节
    novel_state['current_chapter'] = chapter_num
    session['novel_state'] = novel_state
    session.modified = True

    config = novel_state['novel_config']
    is_completed = (
        config.get('total_chapters', 0) > 0 and
        chapter_num >= config.get('total_chapters', 0)
    )
    
    return jsonify({
        'success': True,
        'content': novel_state['chapters_content'][chapter_num],
        'chapter': chapter_num,
        'total_chapters': config.get('total_chapters', 0),
        'is_completed': is_completed,
        'genre': config.get('genre', ''),
        'style': config.get('style', '')
    })


if __name__ == '__main__':
    # 运行应用
    import socket
    socket.setdefaulttimeout(600)  # 设置socket超时为10分钟（图片生成可能需要较长时间）
    
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
