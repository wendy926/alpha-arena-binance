#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deepseekok2.py的独立版本
使用standalone_deepseek_client，不依赖openai包
"""

import os
import sys
import json
import time
import schedule
import requests
from datetime import datetime, timedelta
from standalone_deepseek_client import setup_standalone_deepseek

# 全局变量
web_data = {
    'dashboard': {},
    'kline_data': [],
    'trade_history': [],
    'ai_decisions': [],
    'ai_model_info': {
        'provider': 'deepseek',
        'model': 'deepseek-chat',
        'status': 'unknown',
        'last_check': '',
        'error_message': ''
    }
}

# AI客户端
ai_client = None
_AI_AVAILABLE = False

def setup_ai_client():
    """设置AI客户端"""
    global ai_client, _AI_AVAILABLE
    
    try:
        ai_client = setup_standalone_deepseek()
        if ai_client:
            _AI_AVAILABLE = True
            web_data['ai_model_info'].update({
                'status': 'connected',
                'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error_message': ''
            })
            print("✅ AI客户端设置成功")
        else:
            _AI_AVAILABLE = False
            web_data['ai_model_info'].update({
                'status': 'disabled',
                'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error_message': 'DEEPSEEK_API_KEY未设置'
            })
            print("❌ AI客户端设置失败")
    except Exception as e:
        _AI_AVAILABLE = False
        web_data['ai_model_info'].update({
            'status': 'error',
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error_message': str(e)
        })
        print(f"❌ AI客户端设置错误: {e}")

def test_ai_connection():
    """测试AI连接"""
    global ai_client, _AI_AVAILABLE
    
    if not ai_client:
        web_data['ai_model_info'].update({
            'status': 'disabled',
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error_message': 'AI客户端未初始化'
        })
        return 'disabled'
    
    try:
        response = ai_client.test_connection()
        if response:
            _AI_AVAILABLE = True
            web_data['ai_model_info'].update({
                'status': 'connected',
                'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error_message': ''
            })
            print("✅ AI连接测试成功")
            return 'connected'
        else:
            _AI_AVAILABLE = False
            web_data['ai_model_info'].update({
                'status': 'error',
                'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error_message': '响应为空'
            })
            return 'error'
    except Exception as e:
        _AI_AVAILABLE = False
        web_data['ai_model_info'].update({
            'status': 'error',
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error_message': str(e)
        })
        print(f"❌ AI连接测试失败: {e}")
        return 'error'

def analyze_market_with_ai(price_data, sentiment_data=None, current_pos=None):
    """使用AI分析市场"""
    if not _AI_AVAILABLE or not ai_client:
        print("⚠️ AI功能不可用，返回默认HOLD信号")
        fallback_signal = {
            'signal': 'HOLD',
            'reason': 'AI功能不可用，保持当前状态',
            'confidence': 'LOW',
            'stop_loss': price_data.get('price', 0) * 0.98,
            'take_profit': price_data.get('price', 0) * 1.02,
            'strategy_tag': 'fallback',
            'time_horizon': 'short',
            'risk_budget': 0.01,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 更新AI模型状态
        web_data['ai_model_info'].update({
            'status': 'disabled',
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error_message': 'AI功能不可用'
        })
        
        return fallback_signal
    
    try:
        print("⏳ 正在调用AI分析...")
        
        # 使用独立客户端进行市场分析
        analysis = ai_client.analyze_market(price_data, sentiment_data, current_pos)
        
        # 添加时间戳
        analysis['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 保存AI决策历史
        web_data['ai_decisions'].append(analysis)
        
        # 只保留最近100条记录
        if len(web_data['ai_decisions']) > 100:
            web_data['ai_decisions'] = web_data['ai_decisions'][-100:]
        
        # 更新AI模型状态
        web_data['ai_model_info'].update({
            'status': 'connected',
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error_message': ''
        })
        
        print(f"✓ AI分析完成: {analysis.get('signal')} - {analysis.get('confidence')}")
        return analysis
        
    except Exception as e:
        print(f"❌ AI分析失败: {e}")
        
        # 更新AI模型状态
        web_data['ai_model_info'].update({
            'status': 'error',
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error_message': str(e)
        })
        
        # 返回默认信号
        fallback_signal = {
            'signal': 'HOLD',
            'reason': f'AI分析错误: {str(e)}',
            'confidence': 'LOW',
            'stop_loss': price_data.get('price', 0) * 0.98,
            'take_profit': price_data.get('price', 0) * 1.02,
            'strategy_tag': 'fallback',
            'time_horizon': 'short',
            'risk_budget': 0.01,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        web_data['ai_decisions'].append(fallback_signal)
        return fallback_signal

# 交易所相关功能
exchange = None
_CCXT_AVAILABLE = False

def setup_exchange():
    """设置交易所连接"""
    global exchange, _CCXT_AVAILABLE
    
    try:
        import ccxt
        _CCXT_AVAILABLE = True
        
        # 尝试加载环境变量
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            # 手动读取.env文件
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value
        
        api_key = os.getenv('OKX_API_KEY')
        secret = os.getenv('OKX_SECRET')
        password = os.getenv('OKX_PASSWORD')
        
        if api_key and secret and password:
            exchange = ccxt.okx({
                'apiKey': api_key,
                'secret': secret,
                'password': password,
                'sandbox': True,  # 使用测试环境
                'enableRateLimit': True,
            })
            print("✅ OKX交易所连接设置成功")
        else:
            print("⚠️ OKX API凭证未完整配置，使用模拟数据")
            
    except ImportError:
        _CCXT_AVAILABLE = False
        print("⚠️ ccxt模块不可用，使用模拟数据")
    except Exception as e:
        print(f"❌ 交易所设置失败: {e}")

def get_account_balance():
    """获取账户余额"""
    if not _CCXT_AVAILABLE or not exchange:
        # 返回模拟数据
        return {
            'USDT': {'free': 10000.0, 'used': 0.0, 'total': 10000.0},
            'BTC': {'free': 0.0, 'used': 0.0, 'total': 0.0}
        }
    
    try:
        balance = exchange.fetch_balance()
        return balance
    except Exception as e:
        print(f"❌ 获取余额失败: {e}")
        return {
            'USDT': {'free': 10000.0, 'used': 0.0, 'total': 10000.0},
            'BTC': {'free': 0.0, 'used': 0.0, 'total': 0.0}
        }

def get_btc_price():
    """获取BTC价格"""
    if not _CCXT_AVAILABLE or not exchange:
        # 使用公共API获取价格
        try:
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=10)
            data = response.json()
            return float(data['price'])
        except:
            return 45000.0  # 默认价格
    
    try:
        ticker = exchange.fetch_ticker('BTC/USDT')
        return ticker['last']
    except Exception as e:
        print(f"❌ 获取BTC价格失败: {e}")
        return 45000.0

def update_dashboard_data():
    """更新仪表板数据"""
    try:
        # 获取BTC价格
        current_price = get_btc_price()
        
        # 获取账户余额
        balance = get_account_balance()
        
        # 构建价格数据
        price_data = {
            'price': current_price,
            'price_change': 0.0,  # 简化处理
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # AI分析
        ai_signal = analyze_market_with_ai(price_data)
        
        # 更新仪表板数据
        web_data['dashboard'] = {
            'btc_price': current_price,
            'price_change_24h': 0.0,
            'account_balance': balance,
            'ai_signal': ai_signal,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"✓ 仪表板数据更新完成 - BTC: ${current_price:,.2f}")
        
    except Exception as e:
        print(f"❌ 更新仪表板数据失败: {e}")

def start_scheduler():
    """启动定时任务"""
    # 每分钟更新一次数据
    schedule.every(1).minutes.do(update_dashboard_data)
    
    print("⏰ 定时任务已启动")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    """主函数"""
    print("🚀 启动DeepSeek OKX交易系统（独立版本）...")
    
    # 初始化AI客户端
    setup_ai_client()
    
    # 初始化交易所
    setup_exchange()
    
    # 初始更新数据
    update_dashboard_data()
    
    print("✅ 系统初始化完成")
    
    # 启动定时任务
    start_scheduler()

if __name__ == "__main__":
    main()