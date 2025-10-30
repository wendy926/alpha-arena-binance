#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python 3.6兼容性补丁
修复deepseekok2.py中的openai导入和使用问题
"""

import os
import sys
import json
import requests
from datetime import datetime

# 检测openai版本并选择合适的导入方式
def setup_openai_client():
    """设置OpenAI客户端（兼容Python 3.6）"""
    global ai_client, _OPENAI_AVAILABLE
    
    try:
        import openai
        _OPENAI_AVAILABLE = True
        
        # 检查openai版本
        openai_version = getattr(openai, '__version__', '0.28.1')
        print(f"📦 检测到openai版本: {openai_version}")
        
        # 获取环境变量
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('DEEPSEEK_API_KEY')
        ai_provider = os.getenv('AI_PROVIDER', 'deepseek')
        
        if not api_key:
            print("❌ DEEPSEEK_API_KEY未设置")
            _OPENAI_AVAILABLE = False
            return None
        
        if openai_version.startswith('0.'):
            # 旧版本openai (0.28.x)
            print("🔧 使用旧版openai API (0.28.x)")
            openai.api_key = api_key
            openai.api_base = "https://api.deepseek.com"
            ai_client = openai
        else:
            # 新版本openai (1.x+)
            print("🔧 使用新版openai API (1.x+)")
            from openai import OpenAI
            ai_client = OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com"
            )
        
        return ai_client
        
    except ImportError as e:
        print(f"⚠️ OpenAI模块导入失败: {e}")
        _OPENAI_AVAILABLE = False
        return None

def test_ai_connection_py36():
    """Python 3.6兼容的AI连接测试"""
    if not _OPENAI_AVAILABLE or ai_client is None:
        print("⚠️ AI功能已禁用，跳过连接测试")
        return False
    
    try:
        print("🔍 测试DeepSeek连接...")
        
        # 检查openai版本并使用相应的API
        import openai
        openai_version = getattr(openai, '__version__', '0.28.1')
        
        if openai_version.startswith('0.'):
            # 旧版本API
            response = openai.ChatCompletion.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
                temperature=0.1
            )
            content = response.choices[0].message.content
        else:
            # 新版本API
            response = ai_client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
                temperature=0.1
            )
            content = response.choices[0].message.content
        
        if content:
            print("✅ DeepSeek连接测试成功！")
            return True
        else:
            print("❌ DeepSeek连接测试失败：响应为空")
            return False
            
    except Exception as e:
        print(f"❌ DeepSeek连接测试失败: {e}")
        return False

def analyze_market_with_ai_py36(price_data, sentiment_data=None, current_pos=None):
    """Python 3.6兼容的AI市场分析"""
    if not _OPENAI_AVAILABLE or ai_client is None:
        print("⚠️ AI功能不可用，返回默认HOLD信号")
        return {
            'signal': 'HOLD',
            'reason': 'AI功能不可用，保持当前状态',
            'confidence': 'LOW',
            'stop_loss': price_data.get('price', 0) * 0.98,
            'take_profit': price_data.get('price', 0) * 1.02,
            'strategy_tag': 'fallback',
            'time_horizon': 'short',
            'risk_budget': 0.01
        }
    
    try:
        # 构建简化的prompt
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
        
        print("⏳ 正在调用DeepSeek API...")
        
        # 检查openai版本并使用相应的API
        import openai
        openai_version = getattr(openai, '__version__', '0.28.1')
        
        if openai_version.startswith('0.'):
            # 旧版本API
            response = openai.ChatCompletion.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是专业的量化交易AI，只返回JSON格式的交易建议。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            result = response.choices[0].message.content
        else:
            # 新版本API
            response = ai_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是专业的量化交易AI，只返回JSON格式的交易建议。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            result = response.choices[0].message.content
        
        print("✓ API调用成功")
        print(f"AI响应: {result}")
        
        # 解析JSON响应
        try:
            # 提取JSON部分
            start_idx = result.find('{')
            end_idx = result.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = result[start_idx:end_idx]
                signal_data = json.loads(json_str)
                
                # 验证必需字段
                required_fields = ['signal', 'reason', 'confidence']
                if all(field in signal_data for field in required_fields):
                    # 确保数值字段存在
                    if 'stop_loss' not in signal_data:
                        signal_data['stop_loss'] = price_data.get('price', 0) * 0.98
                    if 'take_profit' not in signal_data:
                        signal_data['take_profit'] = price_data.get('price', 0) * 1.02
                    
                    print(f"✓ 成功解析AI决策: {signal_data.get('signal')} - {signal_data.get('confidence')}")
                    return signal_data
        except json.JSONDecodeError:
            pass
        
        # 如果解析失败，返回默认信号
        print("⚠️ JSON解析失败，使用默认信号")
        return {
            'signal': 'HOLD',
            'reason': 'AI响应解析失败',
            'confidence': 'LOW',
            'stop_loss': price_data.get('price', 0) * 0.98,
            'take_profit': price_data.get('price', 0) * 1.02
        }
        
    except Exception as e:
        print(f"❌ AI分析失败: {e}")
        return {
            'signal': 'HOLD',
            'reason': f'AI分析错误: {str(e)}',
            'confidence': 'LOW',
            'stop_loss': price_data.get('price', 0) * 0.98,
            'take_profit': price_data.get('price', 0) * 1.02
        }

# 全局变量
_OPENAI_AVAILABLE = False
ai_client = None

# 初始化
ai_client = setup_openai_client()

if __name__ == "__main__":
    print("🧪 测试Python 3.6兼容性...")
    test_ai_connection_py36()