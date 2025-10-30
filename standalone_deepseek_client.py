#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完全独立的DeepSeek客户端
不依赖openai包，只使用requests库
适用于任何Python 3.6+环境
"""

import os
import json
import requests
import time
from datetime import datetime

class StandaloneDeepSeekClient:
    """完全独立的DeepSeek客户端"""
    
    def __init__(self, api_key, base_url="https://api.deepseek.com"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'DeepSeek-Client/1.0'
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
            "temperature": temperature,
            "stream": False
        }
        
        try:
            response = requests.post(
                url, 
                headers=self.headers, 
                json=data, 
                timeout=timeout
            )
            
            # 检查HTTP状态码
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            
            result = response.json()
            
            # 检查API响应格式
            if 'choices' not in result or len(result['choices']) == 0:
                raise Exception(f"API响应格式错误: {result}")
            
            return result
            
        except requests.exceptions.Timeout:
            raise Exception("请求超时")
        except requests.exceptions.ConnectionError:
            raise Exception("连接失败")
        except json.JSONDecodeError:
            raise Exception("响应不是有效的JSON格式")
        except Exception as e:
            raise Exception(f"DeepSeek API请求失败: {e}")
    
    def test_connection(self):
        """测试连接"""
        try:
            result = self.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                return content.strip()
            else:
                raise Exception("响应格式错误")
                
        except Exception as e:
            raise Exception(f"连接测试失败: {e}")
    
    def analyze_market(self, price_data, sentiment_data=None, current_pos=None):
        """市场分析"""
        try:
            # 构建分析prompt
            prompt = f"""
分析BTC市场并给出交易建议：

当前价格: ${price_data.get('price', 0):,.2f}
价格变化: {price_data.get('price_change', 0):+.2f}%
时间: {price_data.get('timestamp', '')}

请返回JSON格式的交易建议：
{{
  "signal": "BUY|SELL|HOLD",
  "reason": "分析理由",
  "confidence": "HIGH|MEDIUM|LOW",
  "stop_loss": 止损价格,
  "take_profit": 止盈价格
}}
"""
            
            result = self.chat_completion(
                messages=[
                    {"role": "system", "content": "你是专业的量化交易AI，只返回JSON格式的交易建议。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                return self._parse_trading_signal(content, price_data)
            else:
                raise Exception("API响应格式错误")
                
        except Exception as e:
            # 返回默认信号
            return {
                'signal': 'HOLD',
                'reason': f'AI分析失败: {str(e)}',
                'confidence': 'LOW',
                'stop_loss': price_data.get('price', 0) * 0.98,
                'take_profit': price_data.get('price', 0) * 1.02,
                'strategy_tag': 'fallback',
                'time_horizon': 'short',
                'risk_budget': 0.01
            }
    
    def _parse_trading_signal(self, content, price_data):
        """解析交易信号"""
        try:
            # 提取JSON部分
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = content[start_idx:end_idx]
                signal_data = json.loads(json_str)
                
                # 验证必需字段
                required_fields = ['signal', 'reason', 'confidence']
                if all(field in signal_data for field in required_fields):
                    # 确保数值字段存在
                    if 'stop_loss' not in signal_data:
                        signal_data['stop_loss'] = price_data.get('price', 0) * 0.98
                    if 'take_profit' not in signal_data:
                        signal_data['take_profit'] = price_data.get('price', 0) * 1.02
                    
                    # 添加额外字段
                    signal_data['strategy_tag'] = 'ai_analysis'
                    signal_data['time_horizon'] = 'short'
                    signal_data['risk_budget'] = 0.02
                    
                    return signal_data
        except json.JSONDecodeError:
            pass
        
        # 如果解析失败，返回默认信号
        return {
            'signal': 'HOLD',
            'reason': 'AI响应解析失败',
            'confidence': 'LOW',
            'stop_loss': price_data.get('price', 0) * 0.98,
            'take_profit': price_data.get('price', 0) * 1.02,
            'strategy_tag': 'fallback',
            'time_horizon': 'short',
            'risk_budget': 0.01
        }

def setup_standalone_deepseek():
    """设置独立DeepSeek客户端"""
    try:
        # 尝试加载环境变量
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            # 如果没有python-dotenv，手动读取.env文件
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value
        
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            print("❌ DEEPSEEK_API_KEY未设置")
            return None
        
        client = StandaloneDeepSeekClient(api_key)
        print("✅ 独立DeepSeek客户端初始化成功")
        return client
        
    except Exception as e:
        print(f"❌ DeepSeek客户端初始化失败: {e}")
        return None

def test_standalone_deepseek():
    """测试独立DeepSeek客户端"""
    print("🧪 测试独立DeepSeek客户端...")
    
    client = setup_standalone_deepseek()
    if not client:
        return False
    
    try:
        # 测试连接
        response = client.test_connection()
        print(f"✅ DeepSeek连接成功！响应: {response}")
        
        # 测试市场分析
        test_price_data = {
            'price': 45000.0,
            'price_change': 2.5,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        analysis = client.analyze_market(test_price_data)
        print(f"✅ 市场分析成功！信号: {analysis.get('signal')} - {analysis.get('confidence')}")
        print(f"   理由: {analysis.get('reason')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    test_standalone_deepseek()