#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python 3.6兼容的DeepSeek客户端
使用openai==0.28.1版本的API
"""

import os
import json
import requests
from datetime import datetime

class DeepSeekClient:
    """Python 3.6兼容的DeepSeek客户端"""
    
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
            return response.json()
        except Exception as e:
            raise Exception(f"DeepSeek API请求失败: {e}")
    
    def test_connection(self):
        """测试连接"""
        try:
            result = self.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
        except Exception as e:
            raise Exception(f"连接测试失败: {e}")

def test_deepseek_py36():
    """测试Python 3.6兼容的DeepSeek客户端"""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("❌ DEEPSEEK_API_KEY未设置")
        return False
    
    try:
        client = DeepSeekClient(api_key)
        response = client.test_connection()
        print(f"✅ DeepSeek连接成功！响应: {response}")
        return True
    except Exception as e:
        print(f"❌ DeepSeek连接失败: {e}")
        return False

if __name__ == "__main__":
    test_deepseek_py36()