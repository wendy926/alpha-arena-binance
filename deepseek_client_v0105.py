#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
兼容openai 0.10.5版本的DeepSeek客户端
适用于较老的Python环境
"""

import os
import json
import requests
from datetime import datetime

class DeepSeekClientV0105:
    """兼容openai 0.10.5的DeepSeek客户端"""
    
    def __init__(self, api_key, base_url="https://api.deepseek.com"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def chat_completion(self, model="deepseek-chat", messages=None, max_tokens=1000, temperature=0.1, timeout=30):
        """发送聊天完成请求"""
        if messages is None:
            messages = []
        
        url = f"{self.base_url}/chat/completions"
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = requests.post(
                url, 
                headers=self.headers, 
                json=data, 
                timeout=timeout
            )
            response.raise_for_status()
            result = response.json()
            
            # 模拟openai 0.10.5的响应格式
            class MockResponse:
                def __init__(self, data):
                    self.choices = []
                    if 'choices' in data and len(data['choices']) > 0:
                        choice_data = data['choices'][0]
                        choice = MockChoice(choice_data)
                        self.choices.append(choice)
            
            class MockChoice:
                def __init__(self, choice_data):
                    if 'message' in choice_data:
                        self.message = MockMessage(choice_data['message'])
                    else:
                        self.message = MockMessage({'content': ''})
            
            class MockMessage:
                def __init__(self, message_data):
                    self.content = message_data.get('content', '')
            
            return MockResponse(result)
            
        except Exception as e:
            raise Exception(f"DeepSeek API请求失败: {e}")
    
    def test_connection(self):
        """测试连接"""
        try:
            result = self.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            if result.choices and len(result.choices) > 0:
                return result.choices[0].message.content.strip()
            return ""
        except Exception as e:
            raise Exception(f"连接测试失败: {e}")

def setup_deepseek_v0105():
    """设置DeepSeek客户端（兼容openai 0.10.5）"""
    try:
        # 加载环境变量
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            print("❌ DEEPSEEK_API_KEY未设置")
            return None
        
        client = DeepSeekClientV0105(api_key)
        print("✅ DeepSeek客户端初始化成功")
        return client
        
    except Exception as e:
        print(f"❌ DeepSeek客户端初始化失败: {e}")
        return None

def test_deepseek_v0105():
    """测试DeepSeek连接"""
    client = setup_deepseek_v0105()
    if not client:
        return False
    
    try:
        response = client.test_connection()
        print(f"✅ DeepSeek连接成功！响应: {response}")
        return True
    except Exception as e:
        print(f"❌ DeepSeek连接失败: {e}")
        return False

if __name__ == "__main__":
    test_deepseek_v0105()