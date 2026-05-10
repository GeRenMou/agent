# streamlit run beifen.py
import os
import streamlit as st
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from typing import List, Dict

# 初始化模型 - DeepSeek
model = init_chat_model(

    model="deepseek-chat",
    model_provider="openai",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
    temperature=1.2,
)

# 定义故事智能体的系统提示
STORY_PROMPT = """
你是一个互动故事叙述者，正在讲述一个用户自定义背景的冒险故事。

**严格规则：**
1. **只输出故事情节本身**，不要添加任何额外内容
2. **禁止生成章节标题**（如“第一章”、“场景一”等）
3. **禁止添加说明性文字**（如“以下是故事”、“你来到...”等引导语）
4. 每次只推进一小段情节（50-100字）
5. 每段情节后必须给出4个选项供用户选择：前3个由AI生成，第4个固定为【选项4】自定义行动
6. 选项格式必须严格为：【选项1】描述内容 【选项2】描述内容 【选项3】描述内容 【选项4】自定义行动
7. 每个选项的描述要简洁明了（不超过20字）
8. 用户的选择会影响后续情节和结局
9. 故事要有多个可能的结局（成功、失败、特殊结局等），**必须包含坏结局的可能性**
10. 保持故事的紧张感和趣味性
11. 不要一次性讲完整个故事，要循序渐进
12. 确保前三个选项都有明显的区别
13. **重要**：你必须严格根据用户的实际选择来推进情节，不能臆造用户未做的选择
14. **重要**：如果用户说“我选择：XXX”，你只能基于这个选择继续故事，不能假设用户选择了其他选项
15. 记住用户之前的所有选择，让故事连贯发展
16. 根据历史选择调整情节走向，体现因果关系
17. 当故事达到自然结局时，在回复末尾添加特殊标记：
    - 成功结局：【结局:成功】
    - 失败结局：【结局:失败】
    - 特殊结局：【结局:特殊】
    - 坏结局：【结局:坏结局】
18. 结局章节不需要再提供选项，直接讲述最终结果
19. 根据用户的选择序列合理判断何时应该结束故事，不要无限延续
20. **道具系统**：故事中会出现各种道具，玩家可以选择使用。道具可能帮助也可能阻碍玩家
21. 当出现可以使用道具的时机，在选项中可以包含道具使用选项，格式：【选项X】使用[道具名]...
22. 记录玩家获得的道具，并在合适的时机提示可以使用
23. 坏结局触发条件：错误的选择、忽视警告、过度自信、道德沦丧等都可能导致坏结局

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


def initialize_story():
    """初始化故事状态"""
    return {
        "chapter": 1,
        "choices_made": [],
        "story_history": [],
        "story_summary": "",  # 故事摘要（混合记忆的核心）
        "summary_update_interval": 5,  # 每5章更新一次摘要
        "inventory": [],  # 道具背包
        "story_background": "",  # 故事背景设定
        "ending_type": None,  # 结局类型
        "custom_action_pending": False  # 是否有待处理的自定义行动
    }


def initialize_novel(config: Dict = None):
    """初始化小说状态

    Args:
        config: 小说配置，包含题材、风格、总章数等信息
    """
    if config is None:
        config = {}

    return {
        "current_chapter": 1,
        "total_chapters": config.get("total_chapters", 0),  # 0表示无限章
        "novel_config": config,
        "chapters_content": {},  # {章节号: 内容}
        "novel_summary": "",  # 小说摘要/大纲
        "characters": [],  # 角色列表
        "plot_points": [],  # 关键情节点
        "is_completed": False  # 是否完结
    }


def create_story_agent(thread_id: str = "default"):
    """创建故事智能体（集成InMemorySaver）

    Args:
        thread_id: 会话ID，用于隔离不同故事的记忆
    """
    # 创建内存检查点保存器
    checkpointer = InMemorySaver()

    agent = create_agent(
        model=model,
        tools=[],
        system_prompt=STORY_PROMPT,
        checkpointer=checkpointer  # 集成记忆管理
    )
    return agent


def create_novel_agent(thread_id: str = "default"):
    """创建网文小说智能体（集成InMemorySaver）

    Args:
        thread_id: 会话ID，用于隔离不同小说的记忆
    """
    # 创建内存检查点保存器
    checkpointer = InMemorySaver()

    agent = create_agent(
        model=model,
        tools=[],
        system_prompt=NOVEL_PROMPT,
        checkpointer=checkpointer  # 集成记忆管理
    )
    return agent


def generate_story_segment(agent, user_choice: str = None, thread_id: str = "default",
                           story_background: str = "") -> str:
    """生成故事片段（使用InMemorySaver自动管理记忆）

    Args:
        agent: 故事智能体（已集成InMemorySaver）
        user_choice: 用户当前的选择（如果有）
        thread_id: 会话ID，用于隔离不同故事的记忆
        story_background: 故事背景设定
    """
    # 配置会话ID，LangGraph会自动通过InMemorySaver加载历史记忆
    config = {"configurable": {"thread_id": thread_id}}

    # 准备用户消息
    if user_choice:
        user_message = HumanMessage(content=f"我选择：{user_choice}")
        print(f"[DEBUG] 传递给AI的用户选择: {user_choice}")
    else:
        # 第一次启动故事，传递背景信息
        if story_background:
            initial_prompt = f"""开始故事。以下是故事背景设定：
{story_background}

请根据这个背景开始讲述故事，介绍背景并给出第一个场景的3个选项。"""
        else:
            initial_prompt = "开始故事，请介绍背景并给出第一个场景的3个选项"

        user_message = HumanMessage(content=initial_prompt)
        print("[DEBUG] 开始新故事")

    print(f"[DEBUG] 使用thread_id: {thread_id}，InMemorySaver将自动管理记忆")

    # 使用agent.stream进行流式输出，传入config以启用记忆功能
    response_chunks = []
    for event in agent.stream({"messages": [user_message]}, config=config):
        # LangGraph Agent的事件结构：{'model': {'messages': [AIMessage(...)]}}
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

    ai_response = "".join(response_chunks)
    print(f"[DEBUG] AI响应长度: {len(ai_response)} 字符")
    return ai_response


def generate_novel_chapter(agent, chapter_num: int, novel_config: Dict, thread_id: str = "default") -> str:
    """生成网文章节（使用InMemorySaver自动管理记忆）

    Args:
        agent: 小说智能体（已集成InMemorySaver）
        chapter_num: 当前章节号
        novel_config: 小说配置（题材、风格、总章数等）
        thread_id: 会话ID，用于隔离不同小说的记忆
    """
    # 配置会话ID，LangGraph会自动通过InMemorySaver加载历史记忆
    config = {"configurable": {"thread_id": thread_id}}

    # 构建提示信息，包含小说配置和章节信息
    genre = novel_config.get("genre", "玄幻")
    style = novel_config.get("style", "热血")
    total_chapters = novel_config.get("total_chapters", 0)
    custom_intro = novel_config.get("custom_intro", "")

    if total_chapters > 0:
        chapter_info = f"这是第{chapter_num}章，总共{total_chapters}章"
    else:
        chapter_info = f"这是第{chapter_num}章（无限连载模式）"

    prompt_content = f"""请创作{genre}题材、{style}风格的网络小说。
{chapter_info}。
{f'故事背景：{custom_intro}' if custom_intro else ''}

请确保：
1. 内容与之前章节连贯，保持人物性格和剧情一致性
2. 本章要有足够的吸引力，让读者想继续阅读下一章
3. 章节结尾留下悬念或伏笔
4. 字数控制在800-1500字左右"""

    user_message = HumanMessage(content=prompt_content)
    print(f"[DEBUG] 生成小说第{chapter_num}章，题材:{genre}, 风格:{style}")

    # 使用agent.stream进行流式输出，传入config以启用记忆功能
    response_chunks = []
    for event in agent.stream({"messages": [user_message]}, config=config):
        # LangGraph Agent的事件结构：{'model': {'messages': [AIMessage(...)]}}
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

    ai_response = "".join(response_chunks)
    print(f"[DEBUG] 第{chapter_num}章生成完成，长度: {len(ai_response)} 字符")
    return ai_response


def parse_options(text: str) -> List[str]:
    """从文本中解析选项（支持3-4个选项）"""
    import re

    # 尝试多种解析模式
    # 模式1: 【选项1】... 【选项2】... 【选项3】... 【选项4】...
    options = re.findall(r'【选项\d+】([^【]+)', text)

    # 模式2: 选项1:... 选项2:... 选项3:... 选项4:...
    if not options or len(options) < 3:
        options = re.findall(r'选项\d+[:：]\s*([^选项]+?)(?=选项\d+|$)', text)

    # 模式3: 1. ... 2. ... 3. ... 4. ...
    if not options or len(options) < 3:
        options = re.findall(r'\d+\.\s*([^\d]+?)(?=\d+\.|$)', text)

    # 清理选项文本
    cleaned_options = []
    for opt in options:
        # 去除首尾空白和换行
        opt = opt.strip()
        # 如果选项太长，截取前50个字符
        if len(opt) > 50:
            opt = opt[:50] + "..."
        if opt:
            cleaned_options.append(opt)

    # 如果没有解析到足够的选项，返回空列表（不使用通用选项）
    if len(cleaned_options) < 3:
        print(f"警告: 只解析到 {len(cleaned_options)} 个选项，原文: {text[:200]}")
        return []

    # 确保第4个选项是“自定义行动”
    if len(cleaned_options) >= 4:
        # 如果第4个选项不是自定义行动，添加一个
        if "自定义" not in cleaned_options[3] and "自行" not in cleaned_options[3]:
            cleaned_options[3] = "自定义行动"
    elif len(cleaned_options) == 3:
        # 如果只有3个选项，添加第4个自定义行动
        cleaned_options.append("自定义行动")

    return cleaned_options[:4]


def extract_story_content(text: str) -> str:
    """从AI响应中提取纯故事内容，移除选项部分"""
    import re

    # 移除所有选项格式的内容
    # 模式1: 移除 【选项1】... 【选项2】... 【选项3】...
    cleaned_text = re.sub(r'【选项\d+】[^【]*', '', text)

    # 模式2: 移除 选项1:... 选项2:... 选项3:...
    cleaned_text = re.sub(r'选项\d+[:：][^选项]*', '', cleaned_text)

    # 模式3: 移除结局标记（但保留结局内容）
    cleaned_text = re.sub(r'【结局:(成功|失败|特殊|坏结局)】', '', cleaned_text)

    # 清理多余的空行和空格
    cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)
    cleaned_text = cleaned_text.strip()

    return cleaned_text


def check_ending(text: str) -> str:
    """检查文本中是否包含结局标记，返回结局类型"""
    import re

    # 查找结局标记
    success_match = re.search(r'【结局:成功】', text)
    failure_match = re.search(r'【结局:失败】', text)
    special_match = re.search(r'【结局:特殊】', text)
    bad_match = re.search(r'【结局:坏结局】', text)

    if success_match:
        return "success"
    elif bad_match:
        return "bad"
    elif failure_match:
        return "failure"
    elif special_match:
        return "special"
    else:
        return None


# Streamlit界面
def main():
    st.set_page_config(
        page_title="智慧文娱生成Agent",
        page_icon="📖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 自定义CSS样式
    st.markdown("""
    <style>
    /* 主标题样式 */
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }

    /* 卡片样式 */
    .mode-card {
        padding: 2rem;
        border-radius: 15px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
    }

    .mode-card:hover {
        transform: translateY(-5px);
    }

    /* 故事内容框 - 支持亮色和暗色模式 */
    .story-content {
        padding: 2rem;
        border-radius: 10px;
        border-left: 5px solid #667eea;
        font-size: 1.1rem;
        line-height: 1.8;
    }

    /* 亮色模式下的故事内容 */
    [data-theme="light"] .story-content,
    .stApp[data-theme="light"] .story-content {
        background: linear-gradient(to bottom, #f8f9fa, #e9ecef);
        color: #333;
    }

    /* 暗色模式下的故事内容 */
    [data-theme="dark"] .story-content,
    .stApp[data-theme="dark"] .story-content {
        background: linear-gradient(to bottom, #2d3748, #1a202c);
        color: #e2e8f0;
    }

    /* 选项按钮样式 */
    .stButton > button {
        border-radius: 10px;
        padding: 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }

    /* 功能介绍框 - 支持亮色和暗色模式 */
    .feature-section {
        text-align: center;
        padding: 2rem;
        border-radius: 10px;
    }

    /* 亮色模式下的功能介绍 */
    [data-theme="light"] .feature-section,
    .stApp[data-theme="light"] .feature-section {
        background: #f8f9fa;
        color: #333;
    }

    /* 暗色模式下的功能介绍 */
    [data-theme="dark"] .feature-section,
    .stApp[data-theme="dark"] .feature-section {
        background: #2d3748;
        color: #e2e8f0;
    }

    .feature-section h4 {
        margin-top: 0;
    }

    .feature-section p {
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # 根据当前模式动态显示标题
    if st.session_state.get('selected_mode') == 'interactive':
        st.markdown('<div class="main-title">📖 互动故事生成器</div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="text-align: center; color: #666; margin-bottom: 2rem;">你的每一个选择都将改变故事的走向</div>',
            unsafe_allow_html=True)
    else:
        st.markdown('<div class="main-title">🎬 智慧文娱生成Agent</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center; color: #666; margin-bottom: 2rem;">AI驱动的文娱内容创作平台</div>',
                    unsafe_allow_html=True)

    st.markdown("---")

    # 初始化session state
    if 'story_state' not in st.session_state:
        st.session_state.story_state = initialize_story()
        st.session_state.story_started = False
        st.session_state.current_text = ""
        st.session_state.options = []
        st.session_state.game_over = False
        st.session_state.thread_id = f"story_{id(st.session_state)}"  # 生成唯一的thread_id
        st.session_state.agent = create_story_agent(st.session_state.thread_id)  # 创建带记忆的agent
        st.session_state.selected_mode = None  # 用户选择的模式
        st.session_state.need_regenerate = False  # 是否需要重新生成

        # 网文小说相关状态
        st.session_state.novel_state = initialize_novel()
        st.session_state.novel_started = False
        st.session_state.novel_thread_id = f"novel_{id(st.session_state)}"
        st.session_state.novel_agent = create_novel_agent(st.session_state.novel_thread_id)
        st.session_state.current_chapter_content = ""

    # 主故事区域
    story_container = st.container()

    with story_container:
        # 模式选择界面
        if not st.session_state.get('selected_mode'):
            # 欢迎信息
            st.markdown("""
            <div style='text-align: center; margin-bottom: 3rem;'>
                <h2 style='color: #667eea;'>✨ 探索无限创意世界</h2>
                <p style='font-size: 1.1rem; color: #666;'>选择你喜欢的创作模式，让AI助你开启精彩的故事之旅</p>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("""
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            padding: 2rem; border-radius: 15px; color: white; height: 100%;'>
                    <h3 style='margin-top: 0;'>📖 互动故事</h3>
                    <hr style='border-color: rgba(255,255,255,0.3);'>
                    <ul style='list-style: none; padding-left: 0;'>
                        <li>✓ 自定义故事背景</li>
                        <li>✓ 多分支剧情发展</li>
                        <li>✓ 多种结局</li>
                        <li>✓ AI实时生成内容</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🚀 开始互动故事", type="primary", use_container_width=True, key="mode_interactive",
                             help="点击进入互动故事模式"):
                    st.session_state.selected_mode = "interactive"
                    st.rerun()

            with col2:
                st.markdown("""
                <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                            padding: 2rem; border-radius: 15px; color: white; height: 100%;'>
                    <h3 style='margin-top: 0;'>📚 网文小说</h3>
                    <hr style='border-color: rgba(255,255,255,0.3);'>
                    <ul style='list-style: none; padding-left: 0;'>
                        <li>✓ AI自动连载创作</li>
                        <li>✓ 自定义题材风格</li>
                        <li>✓ 持续章节更新</li>
                        <li>✓ 智能情节规划</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🚀 开始网文创作", type="primary", use_container_width=True, key="mode_novel",
                             help="点击进入网文小说模式"):
                    st.session_state.selected_mode = "novel"
                    st.rerun()

            with col3:
                st.markdown("""
                <div style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                            padding: 2rem; border-radius: 15px; color: white; height: 100%;'>
                    <h3 style='margin-top: 0;'>🎨 漫画模式</h3>
                    <hr style='border-color: rgba(255,255,255,0.3);'>
                    <ul style='list-style: none; padding-left: 0;'>
                        <li>⏳ AI生成分镜脚本</li>
                        <li>⏳ 视觉化叙事</li>
                        <li>⏳ 图文并茂体验</li>
                        <li>⏳ 角色形象设计</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                st.button("⏳ 敬请期待", disabled=True, use_container_width=True, key="mode_comic")

            # 底部功能介绍
            st.markdown("---")
            st.markdown("""
            <div class='feature-section'>
                <h4 style='color: #667eea;'>💡 为什么选择我们？</h4>
                <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 2rem; margin-top: 1.5rem;'>
                    <div>
                        <h5>🤖 智能AI驱动</h5>
                        <p style='font-size: 0.9rem;'>基于先进的AI模型，生成高质量原创内容</p>
                    </div>
                    <div>
                        <h5>🎯 个性化定制</h5>
                        <p style='font-size: 0.9rem;'>根据你的喜好和选择，打造专属故事体验</p>
                    </div>
                    <div>
                        <h5>⚡ 实时交互</h5>
                        <p style='font-size: 0.9rem;'>即时响应，流畅的互动体验</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)


        # 互动故事模式 - 原有的故事逻辑
        elif st.session_state.selected_mode == "interactive":
            # 侧边栏显示故事状态（只在互动故事模式下显示）
            with st.sidebar:
                # 返回主页面按钮固定在顶部
                if st.button("🏠 返回主页面", use_container_width=True, key="back_to_home"):
                    st.session_state.selected_mode = None  # 重置模式选择
                    st.rerun()

                st.markdown("---")
                st.header("📊 故事状态")
                if st.session_state.story_started:
                    state = st.session_state.story_state
                    st.info(f"**章节**: 第{state['chapter']}章")
                    st.info(f"**已做选择**: {len(state['choices_made'])}次")

                    # 显示摘要信息
                    if state.get('story_summary'):
                        with st.expander("📝 故事摘要", expanded=False):
                            st.write(state['story_summary'])
                            st.caption(f"摘要长度: {len(state['story_summary'])} 字符")

                st.markdown("---")
                if st.button("🔄 重新开始故事", type="secondary", use_container_width=True):
                    st.session_state.story_state = initialize_story()
                    st.session_state.story_started = False
                    st.session_state.current_text = ""
                    st.session_state.options = []
                    st.session_state.game_over = False
                    # 生成新的thread_id以清空记忆
                    st.session_state.thread_id = f"story_{id(st.session_state)}_{st.session_state.story_state['chapter']}"
                    st.session_state.agent = create_story_agent(st.session_state.thread_id)  # 重新创建agent
                    st.session_state.need_regenerate = False  # 重置重新生成标志
                    # 注意：不重置 selected_mode，保持在互动故事模式
                    st.rerun()

            if not st.session_state.story_started:
                # 故事背景设置界面
                st.markdown("""
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            padding: 3rem; border-radius: 15px; color: white; margin-bottom: 2rem;'>
                    <h2 style='margin-top: 0;'>🎭 创建你的冒险故事</h2>
                    <hr style='border-color: rgba(255,255,255,0.3);'>
                    <p style='font-size: 1.2rem; line-height: 1.8;'>
                        设定故事的背景和主题，AI将为你生成一个独一无二的互动冒险故事。
                        你的每一个选择都将影响故事的走向和结局！
                    </p>
                </div>
                """, unsafe_allow_html=True)

                # 故事配置表单
                with st.form("story_config_form"):
                    st.subheader("📝 故事设定")

                    story_theme = st.selectbox(
                        "🎯 故事主题",
                        ["奇幻冒险", "科幻探索", "悬疑推理", "恐怖惊悚", "武侠江湖", "末日生存", "宫廷权谋", "校园生活",
                         "自定义"],
                        index=0,
                        help="选择故事的主要题材"
                    )

                    if story_theme == "自定义":
                        custom_theme = st.text_input("请输入自定义主题", placeholder="例如：太空探险、古代战争...")
                        final_theme = custom_theme if custom_theme else "奇幻冒险"
                    else:
                        final_theme = story_theme

                    story_background = st.text_area(
                        "🌍 故事背景（可选）",
                        placeholder="例如：在一个被魔法笼罩的大陆上，你是一名年轻的冒险者...\n或者：2077年，人类已经移民火星，你是一名星际侦探...",
                        height=150,
                        help="提供故事的初始设定或背景介绍，AI会基于此进行创作。留空则使用默认背景。"
                    )

                    difficulty = st.radio(
                        "⚔️ 故事难度",
                        ["简单", "普通", "困难", "地狱"],
                        index=1,
                        help="难度会影响坏结局的触发概率和故事挑战性"
                    )

                    submit_button = st.form_submit_button("🚀 开始冒险", type="primary", use_container_width=True)

                if submit_button:
                    # 保存配置并初始化故事
                    background_info = f"故事主题：{final_theme}，难度：{difficulty}"
                    if story_background:
                        background_info += f"\n背景设定：{story_background}"

                    st.session_state.story_state['story_background'] = background_info
                    st.session_state.story_started = True
                    st.rerun()

            else:
                # 显示故事历史
                if st.session_state.story_state['story_history']:
                    with st.expander("📜 查看故事历史", expanded=False):
                        for i, history in enumerate(st.session_state.story_state['story_history'], 1):
                            st.markdown(f"**第{i}章**: {history}")

                # 生成或显示当前故事片段
                if not st.session_state.current_text:
                    # 使用agent.stream进行流式输出，实时显示生成过程
                    story_placeholder = st.empty()

                    with st.spinner("🎭 故事生成中..."):
                        try:
                            # 确定用户选择
                            user_choice = None
                            if st.session_state.story_state['choices_made']:
                                # 有历史选择，使用最后一次选择
                                user_choice = st.session_state.story_state['choices_made'][-1]

                            # 获取故事背景
                            story_bg = st.session_state.story_state.get('story_background', '')

                            # 调用generate_story_segment，InMemorySaver自动管理记忆
                            full_text = generate_story_segment(
                                st.session_state.agent,
                                user_choice,
                                st.session_state.thread_id,
                                story_bg
                            )

                            # 检查AI响应是否有效
                            if not full_text or len(full_text.strip()) == 0:
                                st.error("❌ AI未返回有效内容，请重试")
                                st.session_state.current_text = "生成失败，请重新尝试"
                                st.session_state.options = []
                                st.rerun()

                            # 流式显示（由于generate_story_segment已经返回完整文本，这里直接显示）
                            story_placeholder.markdown(full_text)

                            # 清除加载动画，保存内容
                            story_placeholder.empty()
                            # 提取纯故事内容（移除选项部分）
                            story_content = extract_story_content(full_text)
                            st.session_state.current_text = story_content
                            parsed_options = parse_options(full_text)

                            # 检查是否解析到足够的选项
                            if not parsed_options and not check_ending(full_text):
                                # 没有解析到选项且不是结局，显示错误并允许重试
                                st.session_state.current_text = story_content + "\n\n⚠️ **警告**：AI未生成有效选项，请重新生成"
                                st.session_state.options = []
                                st.session_state.need_regenerate = True
                            else:
                                st.session_state.options = parsed_options
                                st.session_state.need_regenerate = False

                            # 检查是否到达结局
                            ending_type = check_ending(full_text)
                            if ending_type:
                                st.session_state.game_over = True
                                st.session_state.ending_type = ending_type
                                # 结局不需要选项
                                st.session_state.options = []

                            st.rerun()

                        except Exception as e:
                            print(f"[ERROR] 故事生成失败: {str(e)}")
                            st.error(f"❌ 故事生成失败: {str(e)}")
                            st.info("💡 提示：可能是API连接问题或token限制，请尝试重新开始")
                            st.session_state.current_text = f"生成出错：{str(e)[:200]}"
                            st.session_state.options = []
                            st.rerun()

                # 显示当前故事内容
                st.markdown("### 📖 当前章节")

                st.markdown(f"""
                <div class='story-content'>
                    {st.session_state.current_text}
                </div>
                """, unsafe_allow_html=True)

                # 显示选项按钮
                if st.session_state.options and not st.session_state.game_over:
                    st.markdown("---")
                    st.markdown("""
                    <div style='text-align: center; margin: 2rem 0;'>
                        <h3 style='color: #667eea;'>🎯 做出你的选择</h3>
                        <p style='color: #666;'>谨慎选择，这将决定故事的走向</p>
                    </div>
                    """, unsafe_allow_html=True)

                    # 检查是否有自定义行动待输入
                    custom_action = None
                    if getattr(st.session_state, 'custom_action_pending', False):
                        st.info("💬 请输入你的自定义行动：")
                        custom_action = st.text_input(
                            "你的行动",
                            placeholder="例如：我小心翼翼地观察四周，寻找隐藏的线索...",
                            key="custom_action_input"
                        )

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ 确认行动", type="primary", use_container_width=True):
                                if custom_action and custom_action.strip():
                                    # 记录用户的选择
                                    st.session_state.story_state['choices_made'].append(custom_action)

                                    # 章节递增
                                    st.session_state.story_state['chapter'] += 1

                                    # 清空当前显示，准备生成新内容
                                    st.session_state.current_text = ""
                                    st.session_state.options = []
                                    st.session_state.need_regenerate = False
                                    st.session_state.custom_action_pending = False
                                    st.rerun()
                                else:
                                    st.warning("⚠️ 请输入你的行动内容")

                        with col2:
                            if st.button("❌ 取消", use_container_width=True):
                                st.session_state.custom_action_pending = False
                                st.rerun()

                    else:
                        # 垂直排列选项按钮，显示完整内容（4个选项）
                        for i, option in enumerate(st.session_state.options):
                            # 使用更清晰的按钮标签，显示选项内容
                            button_label = f"{i + 1}. {option}"

                            # 检查是否是自定义行动选项
                            is_custom_action = "自定义" in option or "自行" in option

                            # 自定义行动按钮用不同颜色
                            button_type = "primary" if is_custom_action else "secondary"

                            if st.button(
                                    button_label,
                                    use_container_width=True,
                                    key=f"choice_{st.session_state.story_state['chapter']}_{i}",
                                    type=button_type
                            ):
                                print(
                                    f"[DEBUG] 用户点击按钮 - 章节:{st.session_state.story_state['chapter']}, 选项索引:{i}, 选项内容:{option}")  # 调试信息

                                # 如果是自定义行动选项，显示输入框
                                if is_custom_action:
                                    st.session_state.custom_action_pending = True
                                    st.rerun()
                                else:
                                    # 记录用户的选择（InMemorySaver会自动在下次调用时保存）
                                    st.session_state.story_state['choices_made'].append(option)

                                    # 章节递增
                                    st.session_state.story_state['chapter'] += 1
                                    print(
                                        f"[DEBUG] 更新后的章节: {st.session_state.story_state['chapter']}, choices_made: {st.session_state.story_state['choices_made']}")
                                    print(
                                        f"[DEBUG] Thread ID: {st.session_state.thread_id}，记忆由InMemorySaver自动管理")

                                    # 清空当前显示，准备生成新内容
                                    st.session_state.current_text = ""
                                    st.session_state.options = []
                                    st.session_state.need_regenerate = False
                                    st.rerun()

                # 如果需要重新生成，显示重试按钮
                elif getattr(st.session_state, 'need_regenerate', False):
                    st.markdown("---")
                    st.warning("⚠️ AI未能生成有效选项，请点击下方按钮重新生成")
                    if st.button("🔄 重新生成", type="primary", use_container_width=True):
                        # 清空当前内容，重新生成
                        st.session_state.current_text = ""
                        st.session_state.options = []
                        st.session_state.need_regenerate = False
                        st.rerun()

                # 游戏结束提示
                if st.session_state.game_over:
                    ending_type = getattr(st.session_state, 'ending_type', None)

                    if ending_type == "success":
                        st.success("🎉 恭喜！你成功完成了冒险！")
                        st.markdown("### 🏆 成功结局")
                        st.markdown("**你做出了正确的选择，故事圆满结束！**")
                    elif ending_type == "failure":
                        st.error("💀 很遗憾，冒险失败了...")
                        st.markdown("### 😢 失败结局")
                        st.markdown("**你的选择导致了失败，但你可以重新开始尝试其他路线。**")
                    elif ending_type == "bad":
                        st.error("☠️ 坏结局触发！")
                        st.markdown("### 💀 坏结局")
                        st.markdown("**你的选择导致了最糟糕的结果...也许下次应该更加谨慎？**")
                    elif ending_type == "special":
                        st.info("✨ 你触发了特殊结局！")
                        st.markdown("### 🌟 特殊结局")
                        st.markdown("**故事走向了意想不到的方向...**")
                    else:
                        st.success("🎉 故事已结束！感谢体验！")

                    st.markdown("---")
                    st.markdown("**你可以在左侧重新开始新的冒险！**")

        # 网文小说模式
        elif st.session_state.selected_mode == "novel":
            # 侧边栏显示小说状态
            with st.sidebar:
                # 返回主页面按钮固定在顶部
                if st.button("🏠 返回主页面", use_container_width=True, key="back_to_home_novel"):
                    st.session_state.selected_mode = None  # 重置模式选择
                    st.rerun()

                st.markdown("---")
                st.header("📊 小说信息")

                if st.session_state.novel_started:
                    state = st.session_state.novel_state
                    config = state['novel_config']

                    st.info(f"**当前章节**: 第{state['current_chapter']}章")

                    if state['total_chapters'] > 0:
                        st.info(f"**总章数**: {state['total_chapters']}章")
                        progress = state['current_chapter'] / state['total_chapters']
                        st.progress(min(progress, 1.0))
                    else:
                        st.info("**连载模式**: 无限章节")

                    st.info(f"**题材**: {config.get('genre', '未设置')}")
                    st.info(f"**风格**: {config.get('style', '未设置')}")

                    # 显示已生成章节列表
                    if state['chapters_content']:
                        with st.expander("📑 章节列表", expanded=False):
                            for chap_num in sorted(state['chapters_content'].keys()):
                                st.caption(f"第{chap_num}章")

                st.markdown("---")
                if st.button("🔄 重新创建小说", type="secondary", use_container_width=True):
                    st.session_state.novel_state = initialize_novel()
                    st.session_state.novel_started = False
                    st.session_state.current_chapter_content = ""
                    # 生成新的thread_id以清空记忆
                    st.session_state.novel_thread_id = f"novel_{id(st.session_state)}_{st.session_state.novel_state['current_chapter']}"
                    st.session_state.novel_agent = create_novel_agent(st.session_state.novel_thread_id)
                    st.rerun()

            if not st.session_state.novel_started:
                # 小说配置界面
                st.markdown("""
                <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                            padding: 3rem; border-radius: 15px; color: white; margin-bottom: 2rem;'>
                    <h2 style='margin-top: 0;'>📚 创建你的网络小说</h2>
                    <hr style='border-color: rgba(255,255,255,0.3);'>
                    <p style='font-size: 1.2rem; line-height: 1.8;'>
                        设定小说的题材、风格和背景，AI将为你创作精彩的连载故事。
                        每一章都扣人心弦，让读者欲罢不能！
                    </p>
                </div>
                """, unsafe_allow_html=True)

                # 配置表单
                with st.form("novel_config_form"):
                    col1, col2 = st.columns(2)

                    with col1:
                        genre = st.selectbox(
                            "📖 选择题材",
                            ["玄幻", "都市", "仙侠", "科幻", "历史", "悬疑", "游戏", "灵异", "武侠", "奇幻"],
                            index=0,
                            help="选择小说的主要题材类型"
                        )

                        style = st.selectbox(
                            "🎨 选择风格",
                            ["热血", "轻松", "暗黑", "搞笑", "虐心", "甜宠", "权谋", "种田", "无敌流", "系统流"],
                            index=0,
                            help="选择小说的整体风格基调"
                        )

                    with col2:
                        total_chapters_option = st.radio(
                            "📊 章节模式",
                            ["无限连载", "固定章数"],
                            index=0,
                            help="选择是否限制总章数"
                        )

                        if total_chapters_option == "固定章数":
                            total_chapters = st.number_input(
                                "总章数",
                                min_value=10,
                                max_value=1000,
                                value=100,
                                step=10,
                                help="设置小说的总章节数"
                            )
                        else:
                            total_chapters = 0

                    custom_intro = st.text_area(
                        "📝 故事背景/简介（可选）",
                        placeholder="例如：主角是一个普通的大学生，意外获得了穿越时空的能力...\n或者：在一个修仙世界中，主角从废柴逆袭成为最强者...",
                        height=150,
                        help="提供故事的初始设定或背景介绍，AI会基于此进行创作"
                    )

                    submit_button = st.form_submit_button("🚀 开始创作", type="primary", use_container_width=True)

                if submit_button:
                    # 保存配置并初始化小说
                    novel_config = {
                        "genre": genre,
                        "style": style,
                        "total_chapters": total_chapters,
                        "custom_intro": custom_intro
                    }

                    st.session_state.novel_state = initialize_novel(novel_config)
                    st.session_state.novel_started = True
                    st.rerun()

            else:
                # 小说阅读和生成界面
                state = st.session_state.novel_state
                config = state['novel_config']

                # 显示小说标题和信息
                st.markdown(f"""
                <div style='text-align: center; margin-bottom: 2rem; padding: 1.5rem; 
                            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                            border-radius: 15px; color: white;'>
                    <h2 style='margin: 0;'>{config['genre']}小说 - {config['style']}风格</h2>
                    <p style='margin: 0.5rem 0 0 0; opacity: 0.9;'>
                        {'无限连载模式' if state['total_chapters'] == 0 else f'共{state["total_chapters"]}章'}
                    </p>
                </div>
                """, unsafe_allow_html=True)

                # 如果有自定义简介，显示出来
                if config.get('custom_intro'):
                    with st.expander("📖 故事简介", expanded=False):
                        st.write(config['custom_intro'])

                # 显示当前章节内容
                if st.session_state.current_chapter_content:
                    chapter_num = state['current_chapter']

                    st.markdown(f"### 📄 第{chapter_num}章")
                    st.markdown("---")

                    # 使用美观的样式显示章节内容
                    st.markdown(f"""
                    <div class='story-content' style='border-left-color: #f093fb;'>
                        {st.session_state.current_chapter_content}
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("---")

                    # 检查是否达到总章数
                    is_last_chapter = (
                            state['total_chapters'] > 0 and
                            chapter_num >= state['total_chapters']
                    )

                    if is_last_chapter:
                        # 已完结
                        st.success("🎉 小说已完结！感谢阅读！")
                        st.markdown("**你可以在左侧重新创建新的小说**")
                    else:
                        # 显示下一章按钮
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            if st.button(
                                    "➡️ 下一章",
                                    type="primary",
                                    use_container_width=True,
                                    key=f"next_chapter_{chapter_num}",
                                    help="点击生成下一章内容"
                            ):
                                # 生成下一章
                                next_chapter = chapter_num + 1

                                with st.spinner(f"🎭 正在创作第{next_chapter}章..."):
                                    try:
                                        # 调用生成函数
                                        chapter_content = generate_novel_chapter(
                                            st.session_state.novel_agent,
                                            next_chapter,
                                            config,
                                            st.session_state.novel_thread_id
                                        )

                                        # 检查生成结果
                                        if not chapter_content or len(chapter_content.strip()) == 0:
                                            st.error("❌ AI未返回有效内容，请重试")
                                        else:
                                            # 更新状态
                                            state['current_chapter'] = next_chapter
                                            state['chapters_content'][next_chapter] = chapter_content
                                            st.session_state.current_chapter_content = chapter_content

                                            # 检查是否完结
                                            if state['total_chapters'] > 0 and next_chapter >= state['total_chapters']:
                                                state['is_completed'] = True

                                            st.rerun()

                                    except Exception as e:
                                        print(f"[ERROR] 章节生成失败: {str(e)}")
                                        st.error(f"❌ 章节生成失败: {str(e)}")
                                        st.info("💡 提示：可能是API连接问题，请尝试重试")

                else:
                    # 首次生成第一章
                    st.markdown("### 📄 第1章")
                    st.markdown("---")

                    with st.spinner("🎭 正在创作第一章..."):
                        try:
                            # 生成第一章
                            chapter_content = generate_novel_chapter(
                                st.session_state.novel_agent,
                                1,
                                config,
                                st.session_state.novel_thread_id
                            )

                            # 检查生成结果
                            if not chapter_content or len(chapter_content.strip()) == 0:
                                st.error("❌ AI未返回有效内容，请重试")
                                st.session_state.current_chapter_content = "生成失败，请刷新页面重试"
                            else:
                                # 更新状态
                                state['current_chapter'] = 1
                                state['chapters_content'][1] = chapter_content
                                st.session_state.current_chapter_content = chapter_content
                                st.rerun()

                        except Exception as e:
                            print(f"[ERROR] 第一章生成失败: {str(e)}")
                            st.error(f"❌ 第一章生成失败: {str(e)}")
                            st.info("💡 提示：可能是API连接问题，请尝试重新创建小说")
                            st.session_state.current_chapter_content = f"生成出错：{str(e)[:200]}"


if __name__ == "__main__":
    main()
