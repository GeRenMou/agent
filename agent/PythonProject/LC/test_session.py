"""
测试Session功能的脚本
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

def test_session():
    """测试session功能"""
    with app.test_client() as client:
        print("开始测试Session功能...")
        
        # 测试1: 访问主页
        print("\n1. 测试访问主页...")
        response = client.get('/')
        print(f"   状态码: {response.status_code}")
        assert response.status_code == 200, "主页访问失败"
        print("   ✅ 主页访问成功")
        
        # 测试2: 开始故事
        print("\n2. 测试开始故事...")
        response = client.post('/api/story/start', json={
            'theme': '测试主题',
            'background': '测试背景',
            'difficulty': '普通'
        })
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"   响应: {data.get('success')}")
            if data.get('success'):
                print("   ✅ 故事开始成功")
            else:
                print(f"   ❌ 故事开始失败: {data.get('error')}")
        else:
            print(f"   ❌ 请求失败: {response.data}")
        
        # 测试3: 检查session
        print("\n3. 检查Session状态...")
        with client.session_transaction() as sess:
            print(f"   Session keys: {list(sess.keys())}")
            if 'story_thread_id' in sess:
                print(f"   story_thread_id: {sess['story_thread_id']}")
            if 'story_state' in sess:
                print(f"   story_state存在")
        
        print("\n✅ Session测试完成!")

if __name__ == '__main__':
    test_session()
