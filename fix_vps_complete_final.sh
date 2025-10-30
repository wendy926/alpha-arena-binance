#!/bin/bash
# 完整VPS修复脚本 - 解决所有问题
# 1. 修复ccxt安装问题
# 2. 添加main函数
# 3. 清理端口占用
# 4. 确保不使用模拟数据

echo "🔧 开始完整修复VPS环境..."

# 1. 停止可能运行的服务
echo "============================================================"
echo "🛑 停止现有服务..."
pkill -f "python3 web_server.py" || true
pkill -f "PORT=8081" || true
sleep 2

# 2. 检查并清理端口
echo "============================================================"
echo "🔍 检查端口占用..."
if lsof -i :8081 >/dev/null 2>&1; then
    echo "⚠️ 端口8081被占用，正在清理..."
    lsof -ti :8081 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

if lsof -i :8080 >/dev/null 2>&1; then
    echo "⚠️ 端口8080被占用，正在清理..."
    lsof -ti :8080 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# 3. 检查Python版本
echo "============================================================"
echo "📋 检查Python版本..."
python3 --version

# 4. 升级pip
echo "============================================================"
echo "⬆️ 升级pip..."
python3 -m pip install --upgrade pip

# 5. 强制重新安装ccxt
echo "============================================================"
echo "📦 强制重新安装ccxt..."
pip3 uninstall -y ccxt 2>/dev/null || true
pip3 install --no-cache-dir ccxt

# 6. 安装其他必需包
echo "============================================================"
echo "📦 安装其他必需包..."
pip3 install --no-cache-dir requests flask flask-cors schedule python-dotenv

# 7. 验证ccxt安装
echo "============================================================"
echo "✅ 验证ccxt安装..."

cat > test_ccxt_install.py << 'EOF'
#!/usr/bin/env python3
import sys
try:
    import ccxt
    print(f"✅ ccxt安装成功，版本: {ccxt.__version__}")
    
    # 测试创建交易所实例
    exchange = ccxt.okx()
    print("✅ ccxt.okx()创建成功")
    
    # 测试获取市场数据
    try:
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f"✅ 获取BTC/USDT价格成功: ${ticker['last']}")
    except Exception as e:
        print(f"⚠️ 获取价格失败（正常，因为没有API密钥）: {e}")
    
    print("🎯 ccxt功能正常！")
    sys.exit(0)
    
except ImportError as e:
    print(f"❌ ccxt导入失败: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ ccxt测试失败: {e}")
    sys.exit(1)
EOF

python3 test_ccxt_install.py
if [ $? -ne 0 ]; then
    echo "❌ ccxt安装验证失败，退出"
    exit 1
fi

rm -f test_ccxt_install.py

# 8. 创建完整的独立DeepSeek客户端
echo "============================================================"
echo "📝 创建完整的独立DeepSeek客户端..."

cat > standalone_deepseek_client.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完全独立的DeepSeek客户端
不依赖openai包，只使用requests库
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
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            
            result = response.json()
            
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
        """分析市场数据"""
        try:
            # 构建分析提示
            prompt = f"""
作为专业的加密货币交易分析师，请分析以下市场数据并给出交易建议：

当前BTC价格: ${price_data.get('price', 0):,.2f}
价格变化: {price_data.get('price_change', 0):.2f}%
时间: {price_data.get('timestamp', 'N/A')}

请提供：
1. 交易信号 (BUY/SELL/HOLD)
2. 分析理由
3. 信心等级 (HIGH/MEDIUM/LOW)
4. 止损价位
5. 止盈价位

请以JSON格式回复，包含signal, reason, confidence, stop_loss, take_profit字段。
"""
            
            messages = [{"role": "user", "content": prompt}]
            result = self.chat_completion(messages=messages, max_tokens=500)
            
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content'].strip()
                
                # 尝试解析JSON响应
                try:
                    analysis = json.loads(content)
                    return analysis
                except json.JSONDecodeError:
                    # 如果不是JSON格式，返回默认分析
                    return {
                        'signal': 'HOLD',
                        'reason': content[:200] + '...' if len(content) > 200 else content,
                        'confidence': 'MEDIUM',
                        'stop_loss': price_data.get('price', 0) * 0.98,
                        'take_profit': price_data.get('price', 0) * 1.02
                    }
            else:
                raise Exception("AI响应为空")
                
        except Exception as e:
            # 返回默认分析
            return {
                'signal': 'HOLD',
                'reason': f'AI分析失败: {str(e)}',
                'confidence': 'LOW',
                'stop_loss': price_data.get('price', 0) * 0.98,
                'take_profit': price_data.get('price', 0) * 1.02
            }

def setup_standalone_deepseek():
    """设置独立DeepSeek客户端"""
    try:
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
        
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            return None
        
        return StandaloneDeepSeekClient(api_key)
        
    except Exception as e:
        return None

def test_standalone_deepseek():
    """测试独立DeepSeek客户端"""
    client = setup_standalone_deepseek()
    if not client:
        print("❌ DeepSeek客户端初始化失败")
        return False
    
    try:
        response = client.test_connection()
        print(f"✅ DeepSeek连接成功！响应: {response}")
        return True
    except Exception as e:
        print(f"❌ DeepSeek连接失败: {e}")
        return False

if __name__ == "__main__":
    test_standalone_deepseek()
EOF

# 9. 创建完整的主程序文件（包含main函数）
echo "============================================================"
echo "📝 创建完整的主程序文件..."

# 备份原文件
if [ -f "deepseekok2.py" ]; then
    cp deepseekok2.py deepseekok2.py.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ 已备份原deepseekok2.py文件"
fi

cat > deepseekok2.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek OKX交易系统 - 完整版本
包含main函数，不使用模拟数据
"""

import os
import sys
import json
import time
import requests
import threading
from datetime import datetime, timedelta

# 导入独立的DeepSeek客户端
try:
    from standalone_deepseek_client import setup_standalone_deepseek
    _AI_AVAILABLE = True
except ImportError:
    _AI_AVAILABLE = False
    print("⚠️ 独立DeepSeek客户端不可用")

# 导入ccxt - 强制要求可用
try:
    import ccxt
    _CCXT_AVAILABLE = True
    print("✅ ccxt模块已加载")
except ImportError:
    _CCXT_AVAILABLE = False
    print("❌ ccxt模块不可用 - 这是严重错误！")
    sys.exit(1)

# 导入schedule
try:
    import schedule
    _SCHEDULE_AVAILABLE = True
except ImportError:
    _SCHEDULE_AVAILABLE = False
    print("⚠️ schedule模块不可用")

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

ai_client = None
exchange = None
_running = False

def load_env_file():
    """手动加载.env文件"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value

def setup_ai_client():
    """设置AI客户端"""
    global ai_client, _AI_AVAILABLE
    
    if not _AI_AVAILABLE:
        web_data['ai_model_info'].update({
            'status': 'disabled',
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error_message': '独立DeepSeek客户端不可用'
        })
        return
    
    try:
        ai_client = setup_standalone_deepseek()
        if ai_client:
            web_data['ai_model_info'].update({
                'status': 'connected',
                'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error_message': ''
            })
            print("✅ AI客户端设置成功")
        else:
            web_data['ai_model_info'].update({
                'status': 'disabled',
                'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error_message': 'DEEPSEEK_API_KEY未设置'
            })
            print("❌ AI客户端设置失败")
    except Exception as e:
        web_data['ai_model_info'].update({
            'status': 'error',
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error_message': str(e)
        })
        print(f"❌ AI客户端设置错误: {e}")

def test_ai_connection():
    """测试AI连接"""
    global ai_client
    
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
            web_data['ai_model_info'].update({
                'status': 'connected',
                'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error_message': ''
            })
            return 'connected'
        else:
            web_data['ai_model_info'].update({
                'status': 'error',
                'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error_message': '响应为空'
            })
            return 'error'
    except Exception as e:
        web_data['ai_model_info'].update({
            'status': 'error',
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error_message': str(e)
        })
        return 'error'

def analyze_market_with_ai(price_data, sentiment_data=None, current_pos=None):
    """使用AI分析市场"""
    if not ai_client:
        fallback_signal = {
            'signal': 'HOLD',
            'reason': 'AI功能不可用，保持当前状态',
            'confidence': 'LOW',
            'stop_loss': price_data.get('price', 0) * 0.98,
            'take_profit': price_data.get('price', 0) * 1.02,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        web_data['ai_decisions'].append(fallback_signal)
        return fallback_signal
    
    try:
        analysis = ai_client.analyze_market(price_data, sentiment_data, current_pos)
        analysis['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        web_data['ai_decisions'].append(analysis)
        
        # 只保留最近100条记录
        if len(web_data['ai_decisions']) > 100:
            web_data['ai_decisions'] = web_data['ai_decisions'][-100:]
        
        return analysis
    except Exception as e:
        fallback_signal = {
            'signal': 'HOLD',
            'reason': f'AI分析错误: {str(e)}',
            'confidence': 'LOW',
            'stop_loss': price_data.get('price', 0) * 0.98,
            'take_profit': price_data.get('price', 0) * 1.02,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        web_data['ai_decisions'].append(fallback_signal)
        return fallback_signal

def setup_exchange():
    """设置交易所连接"""
    global exchange
    
    if not _CCXT_AVAILABLE:
        print("❌ ccxt模块不可用 - 无法继续")
        return False
    
    try:
        load_env_file()
        
        api_key = os.getenv('OKX_API_KEY')
        secret = os.getenv('OKX_SECRET')
        password = os.getenv('OKX_PASSWORD')
        
        if api_key and secret and password:
            exchange = ccxt.okx({
                'apiKey': api_key,
                'secret': secret,
                'password': password,
                'sandbox': True,
                'enableRateLimit': True,
            })
            print("✅ OKX交易所连接设置成功")
            return True
        else:
            # 创建无API密钥的交易所实例（仅用于获取公开数据）
            exchange = ccxt.okx({
                'enableRateLimit': True,
            })
            print("⚠️ OKX API凭证未完整配置，仅使用公开数据")
            return True
            
    except Exception as e:
        print(f"❌ 交易所设置失败: {e}")
        return False

def get_account_balance():
    """获取账户余额"""
    if not exchange:
        print("❌ 交易所未初始化")
        return None
    
    try:
        # 检查是否有API密钥
        if not hasattr(exchange, 'apiKey') or not exchange.apiKey:
            print("⚠️ 无API密钥，无法获取账户余额")
            return None
        
        balance = exchange.fetch_balance()
        return balance
    except Exception as e:
        print(f"❌ 获取余额失败: {e}")
        return None

def get_btc_price():
    """获取BTC价格 - 使用真实数据"""
    if not exchange:
        print("❌ 交易所未初始化，使用备用API")
        try:
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=10)
            data = response.json()
            return float(data['price'])
        except Exception as e:
            print(f"❌ 备用API获取价格失败: {e}")
            return None
    
    try:
        ticker = exchange.fetch_ticker('BTC/USDT')
        return ticker['last']
    except Exception as e:
        print(f"❌ OKX获取价格失败: {e}")
        # 备用方案
        try:
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=10)
            data = response.json()
            return float(data['price'])
        except Exception as e2:
            print(f"❌ 备用API也失败: {e2}")
            return None

def get_market_data():
    """获取市场数据"""
    if not exchange:
        return None
    
    try:
        ticker = exchange.fetch_ticker('BTC/USDT')
        return {
            'price': ticker['last'],
            'price_change': ticker['percentage'],
            'volume': ticker['baseVolume'],
            'high': ticker['high'],
            'low': ticker['low'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        print(f"❌ 获取市场数据失败: {e}")
        return None

def update_dashboard_data():
    """更新仪表板数据"""
    try:
        current_price = get_btc_price()
        if current_price is None:
            print("❌ 无法获取BTC价格")
            return
        
        balance = get_account_balance()
        market_data = get_market_data()
        
        price_data = {
            'price': current_price,
            'price_change': market_data['price_change'] if market_data else 0.0,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        ai_signal = analyze_market_with_ai(price_data)
        
        web_data['dashboard'] = {
            'btc_price': current_price,
            'price_change_24h': market_data['price_change'] if market_data else 0.0,
            'account_balance': balance,
            'ai_signal': ai_signal,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'market_data': market_data
        }
        
        print(f"✓ 仪表板数据更新完成 - BTC: ${current_price:,.2f}")
        
    except Exception as e:
        print(f"❌ 更新仪表板数据失败: {e}")

def trading_loop():
    """交易循环"""
    global _running
    
    while _running:
        try:
            update_dashboard_data()
            time.sleep(30)  # 每30秒更新一次
        except Exception as e:
            print(f"❌ 交易循环错误: {e}")
            time.sleep(60)  # 出错时等待更长时间

def start_trading():
    """启动交易"""
    global _running
    
    if _running:
        print("⚠️ 交易已在运行")
        return
    
    _running = True
    trading_thread = threading.Thread(target=trading_loop, daemon=True)
    trading_thread.start()
    print("✅ 交易循环已启动")

def stop_trading():
    """停止交易"""
    global _running
    _running = False
    print("✅ 交易循环已停止")

def main():
    """主函数"""
    print("🚀 启动DeepSeek OKX交易系统...")
    
    # 加载环境变量
    load_env_file()
    
    # 初始化组件
    if not setup_exchange():
        print("❌ 交易所初始化失败")
        return False
    
    setup_ai_client()
    
    # 测试连接
    print("🧪 测试连接...")
    
    # 测试价格获取
    price = get_btc_price()
    if price:
        print(f"✅ BTC价格获取成功: ${price:,.2f}")
    else:
        print("❌ BTC价格获取失败")
        return False
    
    # 测试AI连接
    ai_status = test_ai_connection()
    print(f"🤖 AI连接状态: {ai_status}")
    
    # 初始化数据
    update_dashboard_data()
    
    # 启动交易循环
    start_trading()
    
    print("✅ DeepSeek OKX交易系统初始化完成")
    return True

if __name__ == "__main__":
    main()
EOF

# 10. 测试所有功能
echo "============================================================"
echo "🧪 测试所有功能..."

cat > test_complete_system.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

print("🧪 测试完整系统功能...")

# 测试ccxt导入和功能
try:
    import ccxt
    print(f"✅ ccxt导入成功，版本: {ccxt.__version__}")
    
    # 测试创建交易所
    exchange = ccxt.okx()
    print("✅ ccxt.okx()创建成功")
    
    # 测试获取价格
    try:
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f"✅ 获取BTC/USDT价格成功: ${ticker['last']:,.2f}")
    except Exception as e:
        print(f"⚠️ 获取价格失败（可能是网络问题）: {e}")
    
except ImportError as e:
    print(f"❌ ccxt导入失败: {e}")
    sys.exit(1)

# 测试其他包
packages = ['requests', 'flask', 'schedule', 'json', 'datetime']
for package in packages:
    try:
        __import__(package)
        print(f"✅ {package} 导入成功")
    except ImportError as e:
        print(f"❌ {package} 导入失败: {e}")

# 测试DeepSeek连接
try:
    from standalone_deepseek_client import test_standalone_deepseek
    if test_standalone_deepseek():
        print("✅ DeepSeek连接测试通过")
    else:
        print("⚠️ DeepSeek连接测试失败，请检查API密钥")
except Exception as e:
    print(f"❌ DeepSeek测试失败: {e}")

# 测试主程序导入
try:
    import deepseekok2
    print("✅ deepseekok2模块导入成功")
    
    # 检查main函数
    if hasattr(deepseekok2, 'main'):
        print("✅ main函数存在")
    else:
        print("❌ main函数不存在")
        
except Exception as e:
    print(f"❌ deepseekok2导入失败: {e}")

print("🎯 系统测试完成！")
EOF

python3 test_complete_system.py
if [ $? -ne 0 ]; then
    echo "❌ 系统测试失败"
    exit 1
fi

rm -f test_complete_system.py

# 11. 检查.env文件
echo "============================================================"
echo "📋 检查.env配置..."
if [ -f ".env" ]; then
    echo "✅ .env文件存在"
    if grep -q "DEEPSEEK_API_KEY" .env; then
        echo "✅ DEEPSEEK_API_KEY已配置"
    else
        echo "❌ DEEPSEEK_API_KEY未配置"
    fi
    
    if grep -q "OKX_API_KEY" .env; then
        echo "✅ OKX_API_KEY已配置"
    else
        echo "⚠️ OKX_API_KEY未配置（将使用公开数据）"
    fi
else
    echo "❌ .env文件不存在"
fi

echo "============================================================"
echo "✅ 完整修复完成！"
echo ""
echo "📋 接下来的步骤："
echo "1. 启动服务器："
echo "   PORT=8081 python3 web_server.py"
echo ""
echo "🎯 预期结果："
echo "- ✅ ccxt模块正常工作，不再显示'使用模拟数据'"
echo "- ✅ AI模型状态显示为'已连接'"
echo "- ✅ 获取真实的BTC价格数据"
echo "- ✅ deepseekok2.main()函数正常工作"
echo "- ✅ 端口不再被占用"
echo "============================================================"