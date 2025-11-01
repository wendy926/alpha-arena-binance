import os
import time
import schedule

# 可选导入openai，避免版本兼容问题
try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError as e:
    print(f"警告: openai不可用，AI功能将被禁用: {e}")
    OpenAI = None
    _OPENAI_AVAILABLE = False
"""
为兼容本地较低版本Python环境（如3.7）无法正常导入ccxt的情况，
将ccxt作为可选依赖处理：导入失败时设置为None，并在运行时回退到本地模拟数据。
这不会影响服务器端（Python>=3.8）的正常行为。
"""
try:
    import ccxt as _ccxt
    _CCXT_AVAILABLE = True
except Exception as _ccxt_err:
    _ccxt = None
    _CCXT_AVAILABLE = False
    print(f"警告: ccxt不可用，将使用回退数据: {_ccxt_err}")
import pandas as pd
import re
from dotenv import load_dotenv
import json
import requests
from datetime import datetime, timedelta
load_dotenv()
from paper_trading import (
    init_db,
    record_trade,
    get_last_trade,
    get_last_open_trade,
    list_trades,
    get_all_trades,
    compute_win_rate_from_db,
)

# 初始化AI客户端
# 支持DeepSeek和阿里百炼Qwen
AI_PROVIDER = os.getenv('AI_PROVIDER', 'deepseek').lower()  # 'deepseek' 或 'qwen'

if _OPENAI_AVAILABLE and OpenAI:
    if AI_PROVIDER == 'qwen':
        # 阿里百炼Qwen客户端
        ai_client = OpenAI(
            api_key=os.getenv('DASHSCOPE_API_KEY'),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        AI_MODEL = "qwen-max"
        print(f"使用AI模型: 阿里百炼 {AI_MODEL}")
    else:
        # DeepSeek客户端（默认）
        ai_client = OpenAI(
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com"
        )
        AI_MODEL = "deepseek-chat"
        print(f"使用AI模型: DeepSeek {AI_MODEL}")
    
    # 保持向后兼容
    deepseek_client = ai_client
else:
    print("⚠️ OpenAI不可用，AI功能将被禁用")
    ai_client = None
    deepseek_client = None
    AI_MODEL = "disabled"
    AI_PROVIDER = "none"

# 初始化 Binance USDT-M 永续合约交易所（延迟创建，避免本地无ccxt时报错）
exchange = None

# 内存优化配置
MEMORY_CONFIG = {
    'ai_decisions_limit': 30,      # 从50减少到30
    'trade_history_limit': 50,     # 从100减少到50  
    'profit_curve_limit': 100,     # 从200减少到100
    'signal_history_limit': 20,    # 从30减少到20
    'kline_data_points': 48        # 从96减少到48（12小时数据）
}

# 交易参数配置 - 结合两个版本的优点
TRADE_CONFIG = {
    'symbol': 'BTC/USDT',  # Binance USDT-M 永续合约符号格式
    'amount': 0.01,  # 交易数量 (BTC)
    'leverage': 10,  # 杠杆倍数
    'timeframe': '15m',  # 使用15分钟K线
    'test_mode': False,  # 测试模式
    'data_points': MEMORY_CONFIG['kline_data_points'],  # 优化：12小时数据（48根15分钟K线）
    'analysis_periods': {
        'short_term': 10,  # 短期均线（从20减少到10）
        'medium_term': 20,  # 中期均线（从50减少到20）
        'long_term': MEMORY_CONFIG['kline_data_points']  # 长期趋势（从96减少到48）
    },
    # 执行门槛与防频繁交易参数
    'min_confidence_for_trade': 'MEDIUM',  # 低于该信心不执行
    'signal_cooldown_minutes': 15,         # 信号冷却时间，避免频繁开仓
    'require_signal_confirmation': True    # 首次建仓需近3次里至少2次相同信号
}

# 全局变量存储历史数据
price_history = []
signal_history = []
position = None

# Web展示相关的全局数据存储
web_data = {
    'account_info': {},
    'current_position': None,
    'current_price': 0,
    'trade_history': [],
    'ai_decisions': [],
    'performance': {
        'total_profit': 0,
        'win_rate': 0,
        'total_trades': 0
    },
    'kline_data': [],
    'data_source': None,
    'is_fallback_data': False,
    'timeframe': None,
    'profit_curve': [],  # 收益曲线数据
    'last_update': None,
    'ai_model_info': {
        'provider': AI_PROVIDER,
        'model': AI_MODEL,
        'status': 'unknown',  # unknown, connected, error
        'last_check': None,
        'error_message': None
    }
}

# 初始余额（用于计算收益率）
initial_balance = None
has_run_once = False


def setup_exchange():
    """设置交易所参数（Binance USDM）"""
    global exchange
    try:
        # 如果本地无ccxt，跳过真实交易所初始化，启用回退模式
        if not _CCXT_AVAILABLE:
            print("ccxt不可用：以回退/纸上交易模式运行")
            return True

        # 惰性初始化exchange
        if exchange is None:
            try:
                # 检查是否有API密钥配置
                api_key = os.getenv('BINANCE_API_KEY')
                secret = os.getenv('BINANCE_SECRET_KEY')
                
                if api_key and secret and not TRADE_CONFIG['test_mode']:
                    # 实盘模式：使用API密钥
                    exchange = _ccxt.binanceusdm({
                        'apiKey': api_key,
                        'secret': secret,
                        'enableRateLimit': True,
                        'options': {'defaultType': 'future'}
                    })
                    print("已初始化 Binance USDT-M 期货接口（实盘模式）")
                else:
                    # 模拟模式：不使用API密钥，仅用于获取公开数据
                    exchange = _ccxt.binanceusdm({
                        'enableRateLimit': True,
                        'options': {'defaultType': 'future'}
                    })
                    print("已初始化 Binance USDT-M 期货接口（模拟模式，仅公开数据）")
                    
            except Exception as e_init:
                print(f"初始化交易所失败: {e_init}")
                return False

        # 只有在实盘模式且有API密钥时才设置杠杆和保证金模式
        if not TRADE_CONFIG['test_mode'] and hasattr(exchange, 'apiKey') and exchange.apiKey:
            # 设置杠杆（Binance Futures）
            try:
                exchange.set_leverage(
                    TRADE_CONFIG['leverage'],
                    TRADE_CONFIG['symbol']
                )
                print(f"设置杠杆倍数: {TRADE_CONFIG['leverage']}x")
            except Exception as e_leverage:
                print(f"设置杠杆失败（忽略继续）: {e_leverage}")

            # 设置保证金模式为全仓（如果支持）
            if hasattr(exchange, 'set_margin_mode'):
                try:
                    exchange.set_margin_mode('cross', TRADE_CONFIG['symbol'])
                except Exception as e_margin:
                    print(f"设置保证金模式失败（忽略继续）: {e_margin}")

            # 获取真实余额
            try:
                balance = exchange.fetch_balance()
                usdt_balance = balance.get('USDT', {}).get('free', 0)
                print(f"当前USDT余额: {usdt_balance:.2f}")
            except Exception as e_bal:
                print(f"获取余额失败（忽略继续）: {e_bal}")
        else:
            print("模拟模式：跳过杠杆设置和余额获取，使用模拟数据")

        return True
    except Exception as e:
        print(f"交易所设置失败: {e}")
        return False


def safe_fetch_balance():
    """安全地获取余额，在模拟模式下返回模拟余额"""
    global initial_balance
    
    # 检查是否有API密钥
    binance_api_key = os.getenv('BINANCE_API_KEY')
    binance_secret = os.getenv('BINANCE_SECRET_KEY')
    
    # 如果是测试模式或没有API密钥，返回模拟余额
    if TRADE_CONFIG['test_mode'] or not binance_api_key or not binance_secret:
        simulated_balance = {
            'USDT': {
                'free': 10000.0,
                'used': 0.0,
                'total': 10000.0
            }
        }
        
        # 设置初始余额
        if initial_balance is None:
            initial_balance = 10000.0
            
        return simulated_balance
    
    # 尝试获取真实余额
    try:
        if exchange:
            balance = exchange.fetch_balance()
            return balance
        else:
            raise Exception("Exchange not initialized")
    except Exception as e:
        print(f"获取真实余额失败，使用模拟余额: {e}")
        # 回退到模拟余额
        simulated_balance = {
            'USDT': {
                'free': 10000.0,
                'used': 0.0,
                'total': 10000.0
            }
        }
        
        # 设置初始余额
        if initial_balance is None:
            initial_balance = 10000.0
            
        return simulated_balance


def calculate_technical_indicators(df):
    """计算技术指标 - 来自第一个策略"""
    try:
        # 移动平均线
        df['sma_5'] = df['close'].rolling(window=5, min_periods=1).mean()
        df['sma_20'] = df['close'].rolling(window=20, min_periods=1).mean()
        df['sma_50'] = df['close'].rolling(window=50, min_periods=1).mean()

        # 指数移动平均线
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']

        # 相对强弱指数 (RSI)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # 布林带
        df['bb_middle'] = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

        # 成交量均线
        df['volume_ma'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']

        # 支撑阻力位
        df['resistance'] = df['high'].rolling(20).max()
        df['support'] = df['low'].rolling(20).min()

        # 填充NaN值
        df = df.bfill().ffill()

        return df
    except Exception as e:
        print(f"技术指标计算失败: {e}")
        return df


def get_support_resistance_levels(df, lookback=20):
    """计算支撑阻力位"""
    try:
        recent_high = df['high'].tail(lookback).max()
        recent_low = df['low'].tail(lookback).min()
        current_price = df['close'].iloc[-1]

        resistance_level = recent_high
        support_level = recent_low

        # 动态支撑阻力（基于布林带）
        bb_upper = df['bb_upper'].iloc[-1]
        bb_lower = df['bb_lower'].iloc[-1]

        return {
            'static_resistance': resistance_level,
            'static_support': support_level,
            'dynamic_resistance': bb_upper,
            'dynamic_support': bb_lower,
            'price_vs_resistance': ((resistance_level - current_price) / current_price) * 100,
            'price_vs_support': ((current_price - support_level) / support_level) * 100
        }
    except Exception as e:
        print(f"支撑阻力计算失败: {e}")
        return {}


def get_sentiment_indicators():
    """获取情绪指标 - 简洁版本"""
    try:
        API_URL = "https://service.cryptoracle.network/openapi/v2/endpoint"
        API_KEY = "b54bcf4d-1bca-4e8e-9a24-22ff2c3d76d5"

        # 获取最近4小时数据
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=4)

        request_body = {
            "apiKey": API_KEY,
            "endpoints": ["CO-A-02-01", "CO-A-02-02"],  # 只保留核心指标
            "startTime": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "endTime": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "timeType": "15m",
            "token": ["BTC"]
        }

        headers = {"Content-Type": "application/json", "X-API-KEY": API_KEY}
        response = requests.post(API_URL, json=request_body, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200 and data.get("data"):
                time_periods = data["data"][0]["timePeriods"]

                # 查找第一个有有效数据的时间段
                for period in time_periods:
                    period_data = period.get("data", [])

                    sentiment = {}
                    valid_data_found = False

                    for item in period_data:
                        endpoint = item.get("endpoint")
                        value = item.get("value", "").strip()

                        if value:  # 只处理非空值
                            try:
                                if endpoint in ["CO-A-02-01", "CO-A-02-02"]:
                                    sentiment[endpoint] = float(value)
                                    valid_data_found = True
                            except (ValueError, TypeError):
                                continue

                    # 如果找到有效数据
                    if valid_data_found and "CO-A-02-01" in sentiment and "CO-A-02-02" in sentiment:
                        positive = sentiment['CO-A-02-01']
                        negative = sentiment['CO-A-02-02']
                        net_sentiment = positive - negative

                        # 正确的时间延迟计算
                        data_delay = int((datetime.now() - datetime.strptime(
                            period['startTime'], '%Y-%m-%d %H:%M:%S')).total_seconds() // 60)

                        print(f"✅ 使用情绪数据时间: {period['startTime']} (延迟: {data_delay}分钟)")

                        return {
                            'positive_ratio': positive,
                            'negative_ratio': negative,
                            'net_sentiment': net_sentiment,
                            'data_time': period['startTime'],
                            'data_delay_minutes': data_delay
                        }

                print("❌ 所有时间段数据都为空")
                return None

        return None
    except Exception as e:
        print(f"情绪指标获取失败: {e}")
        return None


def get_market_trend(df):
    """判断市场趋势"""
    try:
        current_price = df['close'].iloc[-1]

        # 多时间框架趋势分析
        trend_short = "上涨" if current_price > df['sma_20'].iloc[-1] else "下跌"
        trend_medium = "上涨" if current_price > df['sma_50'].iloc[-1] else "下跌"

        # MACD趋势
        macd_trend = "bullish" if df['macd'].iloc[-1] > df['macd_signal'].iloc[-1] else "bearish"

        # 综合趋势判断
        if trend_short == "上涨" and trend_medium == "上涨":
            overall_trend = "强势上涨"
        elif trend_short == "下跌" and trend_medium == "下跌":
            overall_trend = "强势下跌"
        else:
            overall_trend = "震荡整理"

        return {
            'short_term': trend_short,
            'medium_term': trend_medium,
            'macd': macd_trend,
            'overall': overall_trend,
            'rsi_level': df['rsi'].iloc[-1]
        }
    except Exception as e:
        print(f"趋势分析失败: {e}")
        return {}


def get_real_btc_price():
    """获取实时BTC价格，用于fallback数据"""
    try:
        # 尝试从多个公共API获取实时BTC价格
        apis = [
            "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
            "https://api.coinbase.com/v2/exchange-rates?currency=BTC",
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        ]
        
        for api_url in apis:
            try:
                response = requests.get(api_url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    
                    if "binance" in api_url:
                        price = float(data['price'])
                        print(f"✅ 从Binance获取实时BTC价格: ${price:,.2f}")
                        return price
                    elif "coinbase" in api_url:
                        price = float(data['data']['rates']['USD'])
                        print(f"✅ 从Coinbase获取实时BTC价格: ${price:,.2f}")
                        return price
                    elif "coingecko" in api_url:
                        price = float(data['bitcoin']['usd'])
                        print(f"✅ 从CoinGecko获取实时BTC价格: ${price:,.2f}")
                        return price
            except Exception as e:
                print(f"⚠️ API {api_url} 失败: {e}")
                continue
                
        print("⚠️ 所有价格API都失败，使用默认价格")
        return 68000  # 最后的备用价格
        
    except Exception as e:
        print(f"⚠️ 获取实时价格失败: {e}")
        return 68000

def generate_fallback_ohlcv_data():
    """生成fallback OHLCV数据，用于网络连接失败时"""
    import random
    import numpy as np
    
    print("🔄 网络连接失败，使用本地模拟数据...")
    
    # 获取实时BTC价格作为基础价格
    base_price = get_real_btc_price()
    data_points = TRADE_CONFIG['data_points']
    
    # 生成时间序列
    now = datetime.now()
    timestamps = []
    for i in range(data_points):
        timestamp = now - timedelta(minutes=15 * (data_points - 1 - i))
        timestamps.append(int(timestamp.timestamp() * 1000))
    
    # 生成OHLCV数据（模拟真实的价格波动）
    ohlcv = []
    current_price = base_price
    
    for i, timestamp in enumerate(timestamps):
        # 模拟价格波动（-2% 到 +2%）
        price_change = random.uniform(-0.02, 0.02)
        current_price = current_price * (1 + price_change)
        
        # 生成OHLC
        volatility = random.uniform(0.005, 0.015)  # 0.5% - 1.5% 波动
        high = current_price * (1 + volatility)
        low = current_price * (1 - volatility)
        open_price = current_price * random.uniform(0.995, 1.005)
        close_price = current_price
        
        # 生成成交量
        volume = random.uniform(100, 1000)
        
        ohlcv.append([timestamp, open_price, high, low, close_price, volume])
    
    return ohlcv

def get_btc_ohlcv_enhanced():
    """增强版：获取BTC K线数据并计算技术指标（以 Binance FAPI 为主）"""
    try:
        # 本地无ccxt时，直接使用fallback数据
        if not _CCXT_AVAILABLE:
            fallback_ohlcv = generate_fallback_ohlcv_data()
            df = pd.DataFrame(fallback_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = calculate_technical_indicators(df)

            current_data = df.iloc[-1]
            previous_data = df.iloc[-2]

            trend_analysis = get_market_trend(df)
            levels_analysis = get_support_resistance_levels(df)

            return {
                'price': current_data['close'],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'high': current_data['high'],
                'low': current_data['low'],
                'volume': current_data['volume'],
                'timeframe': TRADE_CONFIG['timeframe'],
                'price_change': ((current_data['close'] - previous_data['close']) / previous_data['close']) * 100,
                'kline_data': df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].tail(10).to_dict('records'),
                'technical_data': {
                    'sma_5': current_data.get('sma_5', 0),
                    'sma_20': current_data.get('sma_20', 0),
                    'sma_50': current_data.get('sma_50', 0),
                    'rsi': current_data.get('rsi', 0),
                    'macd': current_data.get('macd', 0),
                    'macd_signal': current_data.get('macd_signal', 0),
                    'macd_histogram': current_data.get('macd_histogram', 0),
                    'bb_upper': current_data.get('bb_upper', 0),
                    'bb_lower': current_data.get('bb_lower', 0),
                    'bb_position': current_data.get('bb_position', 0),
                    'volume_ratio': current_data.get('volume_ratio', 0)
                },
                'trend_analysis': trend_analysis,
                'levels_analysis': levels_analysis,
                'full_data': df,
                'data_source': 'fallback-local',
                'is_fallback_data': True
            }

        # 预加载交易所市场，避免符号不识别（exchange可能未初始化）
        if exchange:
            try:
                exchange.load_markets()
            except Exception as e:
                print(f"加载市场失败(忽略继续): {e}")

        ohlcv = None
        data_source = None

        # 主数据源：Binance USDM 永续（优先使用配置符号）
        try:
            ohlcv = exchange.fetch_ohlcv(
                TRADE_CONFIG['symbol'], TRADE_CONFIG['timeframe'],
                limit=TRADE_CONFIG['data_points']
            )
            data_source = getattr(exchange, 'id', 'binanceusdm')
        except Exception as e1:
            print(f"fetch_ohlcv失败({TRADE_CONFIG['symbol']}): {e1}，尝试现货BTC/USDT")
            try:
                ohlcv = exchange.fetch_ohlcv(
                    'BTC/USDT', TRADE_CONFIG['timeframe'],
                    limit=TRADE_CONFIG['data_points']
                )
                data_source = getattr(exchange, 'id', 'binance')
            except Exception as e2:
                print(f"获取增强K线数据失败: {e2}")

        # 如果主路径成功，直接返回
        if ohlcv:
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = calculate_technical_indicators(df)

            current_data = df.iloc[-1]
            previous_data = df.iloc[-2]

            trend_analysis = get_market_trend(df)
            levels_analysis = get_support_resistance_levels(df)

            return {
                'price': current_data['close'],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'high': current_data['high'],
                'low': current_data['low'],
                'volume': current_data['volume'],
                'timeframe': TRADE_CONFIG['timeframe'],
                'price_change': ((current_data['close'] - previous_data['close']) / previous_data['close']) * 100,
                'kline_data': df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].tail(10).to_dict('records'),
                'technical_data': {
                    'sma_5': current_data.get('sma_5', 0),
                    'sma_20': current_data.get('sma_20', 0),
                    'sma_50': current_data.get('sma_50', 0),
                    'rsi': current_data.get('rsi', 0),
                    'macd': current_data.get('macd', 0),
                    'macd_signal': current_data.get('macd_signal', 0),
                    'macd_histogram': current_data.get('macd_histogram', 0),
                    'bb_upper': current_data.get('bb_upper', 0),
                    'bb_lower': current_data.get('bb_lower', 0),
                    'bb_position': current_data.get('bb_position', 0),
                    'volume_ratio': current_data.get('volume_ratio', 0)
                },
                'trend_analysis': trend_analysis,
                'levels_analysis': levels_analysis,
                'full_data': df,
                'data_source': data_source
            }

        # 备用数据源：直接使用 Binance USDM
        try:
            print("🔁 尝试使用Binance USDT-M期货数据作为备用数据源")
            binance = _ccxt.binanceusdm({'options': {'defaultType': 'future'}})
            try:
                binance.load_markets()
            except Exception as be:
                print(f"Binance市场加载失败(忽略继续): {be}")
            ohlcv = binance.fetch_ohlcv('BTC/USDT', TRADE_CONFIG['timeframe'],
                                        limit=TRADE_CONFIG['data_points'])
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = calculate_technical_indicators(df)

            current_data = df.iloc[-1]
            previous_data = df.iloc[-2]

            trend_analysis = get_market_trend(df)
            levels_analysis = get_support_resistance_levels(df)

            return {
                'price': current_data['close'],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'high': current_data['high'],
                'low': current_data['low'],
                'volume': current_data['volume'],
                'timeframe': TRADE_CONFIG['timeframe'],
                'price_change': ((current_data['close'] - previous_data['close']) / previous_data['close']) * 100,
                'kline_data': df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].tail(10).to_dict('records'),
                'technical_data': {
                    'sma_5': current_data.get('sma_5', 0),
                    'sma_20': current_data.get('sma_20', 0),
                    'sma_50': current_data.get('sma_50', 0),
                    'rsi': current_data.get('rsi', 0),
                    'macd': current_data.get('macd', 0),
                    'macd_signal': current_data.get('macd_signal', 0),
                    'macd_histogram': current_data.get('macd_histogram', 0),
                    'bb_upper': current_data.get('bb_upper', 0),
                    'bb_lower': current_data.get('bb_lower', 0),
                    'bb_position': current_data.get('bb_position', 0),
                    'volume_ratio': current_data.get('volume_ratio', 0)
                },
                'trend_analysis': trend_analysis,
                'levels_analysis': levels_analysis,
                'full_data': df,
                'data_source': 'binanceusdm'
            }
        except Exception as be2:
            print(f"Binance备用数据源获取失败: {be2}")

        # 使用本地fallback数据
        try:
            fallback_ohlcv = generate_fallback_ohlcv_data()
            df = pd.DataFrame(fallback_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = calculate_technical_indicators(df)

            current_data = df.iloc[-1]
            previous_data = df.iloc[-2]

            trend_analysis = get_market_trend(df)
            levels_analysis = get_support_resistance_levels(df)

            return {
                'price': current_data['close'],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'high': current_data['high'],
                'low': current_data['low'],
                'volume': current_data['volume'],
                'timeframe': TRADE_CONFIG['timeframe'],
                'price_change': ((current_data['close'] - previous_data['close']) / previous_data['close']) * 100,
                'kline_data': df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].tail(10).to_dict('records'),
                'technical_data': {
                    'sma_5': current_data.get('sma_5', 0),
                    'sma_20': current_data.get('sma_20', 0),
                    'sma_50': current_data.get('sma_50', 0),
                    'rsi': current_data.get('rsi', 0),
                    'macd': current_data.get('macd', 0),
                    'macd_signal': current_data.get('macd_signal', 0),
                    'macd_histogram': current_data.get('macd_histogram', 0),
                    'bb_upper': current_data.get('bb_upper', 0),
                    'bb_lower': current_data.get('bb_lower', 0),
                    'bb_position': current_data.get('bb_position', 0),
                    'volume_ratio': current_data.get('volume_ratio', 0)
                },
                'trend_analysis': trend_analysis,
                'levels_analysis': levels_analysis,
                'full_data': df,
                'is_fallback_data': True
            }
        except Exception as fallback_error:
            print(f"生成fallback数据也失败: {fallback_error}")
            return None
    except Exception as e_all:
        print(f"获取增强K线数据整体失败: {e_all}")
        import traceback
        traceback.print_exc()
        return None

def generate_technical_analysis_text(price_data):
    """生成技术分析文本"""
    if 'technical_data' not in price_data:
        return "技术指标数据不可用"

    tech = price_data['technical_data']
    trend = price_data.get('trend_analysis', {})
    levels = price_data.get('levels_analysis', {})

    # 检查数据有效性
    def safe_float(value, default=0):
        return float(value) if value and pd.notna(value) else default

    analysis_text = f"""
    【技术指标分析】
    📈 移动平均线:
    - 5周期: {safe_float(tech['sma_5']):.2f} | 价格相对: {(price_data['price'] - safe_float(tech['sma_5'])) / safe_float(tech['sma_5']) * 100:+.2f}%
    - 20周期: {safe_float(tech['sma_20']):.2f} | 价格相对: {(price_data['price'] - safe_float(tech['sma_20'])) / safe_float(tech['sma_20']) * 100:+.2f}%
    - 50周期: {safe_float(tech['sma_50']):.2f} | 价格相对: {(price_data['price'] - safe_float(tech['sma_50'])) / safe_float(tech['sma_50']) * 100:+.2f}%

    🎯 趋势分析:
    - 短期趋势: {trend.get('short_term', 'N/A')}
    - 中期趋势: {trend.get('medium_term', 'N/A')}
    - 整体趋势: {trend.get('overall', 'N/A')}
    - MACD方向: {trend.get('macd', 'N/A')}

    📊 动量指标:
    - RSI: {safe_float(tech['rsi']):.2f} ({'超买' if safe_float(tech['rsi']) > 70 else '超卖' if safe_float(tech['rsi']) < 30 else '中性'})
    - MACD: {safe_float(tech['macd']):.4f}
    - 信号线: {safe_float(tech['macd_signal']):.4f}

    🎚️ 布林带位置: {safe_float(tech['bb_position']):.2%} ({'上部' if safe_float(tech['bb_position']) > 0.7 else '下部' if safe_float(tech['bb_position']) < 0.3 else '中部'})

    💰 关键水平:
    - 静态阻力: {safe_float(levels.get('static_resistance', 0)):.2f}
    - 静态支撑: {safe_float(levels.get('static_support', 0)):.2f}
    """
    return analysis_text

def build_ai_prompt(price_data, last_signal=None, sentiment_data=None, current_pos=None):
    """构建更结构化的AI Prompt，参考AI-Trader风格并结合本项目数据。"""
    tf = TRADE_CONFIG['timeframe']
    # K线摘要（最近5根）
    kline_text = f"【最近5根{tf}K线】\n"
    try:
        for i, k in enumerate(price_data.get('kline_data', [])[-5:]):
            trend = "阳线" if (k.get('close', 0) > k.get('open', 0)) else "阴线"
            change = 0.0
            if k.get('open', 0):
                change = ((k['close'] - k['open']) / k['open']) * 100
            kline_text += f"K{i+1}: {trend} 开:{k.get('open',0):.2f} 收:{k.get('close',0):.2f} 涨跌:{change:+.2f}%\n"
    except Exception:
        kline_text += "(K线数据不可用)\n"

    # 技术分析文本
    technical_analysis = generate_technical_analysis_text(price_data)

    # 上次信号
    signal_text = ""
    if last_signal:
        signal_text = f"【上次信号】{last_signal.get('signal','N/A')} / {last_signal.get('confidence','N/A')}"

    # 情绪文本
    if sentiment_data:
        sign = '+' if sentiment_data.get('net_sentiment', 0) >= 0 else ''
        sentiment_text = f"【市场情绪】乐观{sentiment_data.get('positive_ratio',0):.1%} 悲观{sentiment_data.get('negative_ratio',0):.1%} 净值{sign}{sentiment_data.get('net_sentiment',0):.3f}"
    else:
        sentiment_text = "【市场情绪】数据暂不可用"

    # 持仓文本
    if current_pos:
        position_text = f"{current_pos.get('side')}仓, 数量:{current_pos.get('size')} 盈亏:{current_pos.get('unrealized_pnl',0):.2f}USDT"
        pnl_text = f", 持仓盈亏:{current_pos.get('unrealized_pnl',0):.2f} USDT"
    else:
        position_text = "无持仓"
        pnl_text = ""

    # 组合Prompt（严格的结构与输出要求）
    prompt = f"""
[角色]
你是专业量化交易AI，专注{tf}周期的趋势与风险控制。

[输入数据]
{kline_text}
{technical_analysis}
{signal_text}
{sentiment_text}

[当前行情]
- 当前价格: ${price_data.get('price',0):,.2f}
- 时间: {price_data.get('timestamp','')}
- 当根最高/最低: {price_data.get('high',0):.2f} / {price_data.get('low',0):.2f}
- 成交量: {price_data.get('volume',0):.2f}
- 价格变化: {price_data.get('price_change',0):+.2f}%
- 当前持仓: {position_text}{pnl_text}

[思考标准]
1. 趋势持续性优先：避免因单根K线改变整体判断。
2. 反转需多指标共振：至少2~3项技术指标同向确认再反转。
3. 情绪仅作辅助：与技术同向增强信心；背离以技术为主。
4. 风险明确：给出合理止损/止盈，方向与多空逻辑一致。
5. 防频繁交易：若无明确趋势，输出HOLD。

[输出格式]
仅输出一个JSON对象（不含任何额外文字或注释）：
{{
  "signal": "BUY|SELL|HOLD",
  "reason": "简要分析理由(趋势、关键位、指标共振)",
  "stop_loss": <number>,
  "take_profit": <number>,
  "confidence": "HIGH|MEDIUM|LOW",
  "strategy_tag": "trend_follow|mean_reversion|breakout|other",
  "time_horizon": "scalp|intraday|swing",
  "risk_budget": "low|medium|high"
}}

[校验规则]
- 多头：stop_loss < 当前价 < take_profit。
- 空头：take_profit < 当前价 < stop_loss。
- HOLD时给出中性理由，止损/止盈可贴近当前价或留空。
"""
    return prompt


def get_current_position():
    """获取当前持仓情况 - Binance FAPI 版本"""
    try:
        # 在测试模式下或没有API密钥时，使用模拟持仓数据
        if TRADE_CONFIG.get('test_mode', True) or exchange is None:
            print("使用模拟持仓数据（测试模式）")
            return compute_paper_position()
        
        # 检查是否有API密钥
        binance_api_key = os.getenv('BINANCE_API_KEY')
        binance_secret_key = os.getenv('BINANCE_SECRET_KEY')
        if not binance_api_key or not binance_secret_key:
            print("缺少API密钥，使用模拟持仓数据")
            return compute_paper_position()
        
        positions = exchange.fetch_positions([TRADE_CONFIG['symbol']])

        for pos in positions:
            if pos.get('symbol') == TRADE_CONFIG['symbol']:
                contracts = pos.get('contracts')
                if contracts is None:
                    contracts = pos.get('positionAmt')
                contracts = float(contracts) if contracts else 0.0

                if contracts > 0:
                    entry_price = pos.get('entryPrice') or pos.get('avgPrice') or 0
                    unrealized_pnl = pos.get('unrealizedPnl') or 0
                    leverage = pos.get('leverage') or TRADE_CONFIG['leverage']
                    side = pos.get('side')  # 统一字段：'long' 或 'short'

                    return {
                        'side': side,
                        'size': contracts,
                        'entry_price': float(entry_price),
                        'unrealized_pnl': float(unrealized_pnl),
                        'leverage': float(leverage),
                        'symbol': pos.get('symbol')
                    }

        return None

    except Exception as e:
        print(f"获取持仓失败，使用模拟持仓数据: {e}")
        return compute_paper_position()


def compute_paper_position(current_price=None):
    """基于纸上交易记录推导当前持仓（用于无交易所/测试模式）"""
    try:
        # 优先使用内存中的交易历史来判断是否已平仓
        history = web_data.get('trade_history', [])
        last_open = None
        last_open_idx = None
        for idx in range(len(history) - 1, -1, -1):
            act = (history[idx] or {}).get('action')
            if act in ('open_long', 'open_short'):
                last_open = history[idx]
                last_open_idx = idx
                break
        if last_open is None:
            # 回退到数据库最近开仓/交易
            last = get_last_open_trade() or get_last_trade()
            if not last or last.get('action') not in ('open_long', 'open_short'):
                return None
            last_open = last
            last_open_idx = None

        # 如果在最近开仓之后存在 close_* 或 再次 open_*（反转），则视为已平仓
        if last_open_idx is not None:
            closed = False
            for j in range(last_open_idx + 1, len(history)):
                aj = (history[j] or {}).get('action')
                if aj in ('close_long', 'close_short', 'open_long', 'open_short'):
                    closed = True
                    break
            if closed:
                return None

        action = last_open.get('action')
        entry_price = to_float(last_open.get('price'), 0.0)
        amount = to_float(last_open.get('amount'), 0.0)
        if amount <= 0 or entry_price <= 0:
            return None
        cur_price = to_float(current_price if current_price is not None else web_data.get('current_price', entry_price), entry_price)
        if action == 'open_long':
            side = 'long'
            pnl = (cur_price - entry_price) * amount
        else:
            side = 'short'
            pnl = (entry_price - cur_price) * amount
        return {
            'side': side,
            'size': amount,
            'entry_price': entry_price,
            'unrealized_pnl': pnl,
            'leverage': TRADE_CONFIG['leverage'],
            'symbol': TRADE_CONFIG['symbol']
        }
    except Exception as e:
        print(f"计算纸上持仓失败: {e}")
        return None


def safe_json_parse(json_str):
    """安全解析JSON，处理格式不规范的情况"""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        try:
            # 尝试提取JSON代码块（如果AI包在```json```中）
            if '```json' in json_str:
                start = json_str.find('```json') + 7
                end = json_str.find('```', start)
                if end != -1:
                    json_str = json_str[start:end].strip()
            elif '```' in json_str:
                start = json_str.find('```') + 3
                end = json_str.find('```', start)
                if end != -1:
                    json_str = json_str[start:end].strip()
            
            # 尝试直接解析
            try:
                return json.loads(json_str)
            except:
                pass
            
            # 修复常见的JSON格式问题
            json_str = json_str.replace("'", '"')
            json_str = re.sub(r'(\w+):', r'"\1":', json_str)
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"JSON解析失败，原始内容: {json_str[:200]}")
            print(f"错误详情: {e}")
            return None


def to_float(value, default=0.0):
    """将输入安全转换为float，无法解析则返回默认值"""
    try:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            s = value.strip().replace(',', '')
            m = re.search(r'[-+]?\d*\.?\d+', s)
            if m:
                return float(m.group())
        return default
    except Exception:
        return default


def compute_win_rate_from_history():
    """从内存中的 trade_history 计算胜率和已完成交易数。
    规则：
    - 将方向反转（open_long -> open_short 或 open_short -> open_long）视为上一次持仓的平仓事件；
    - 将显式的 close_long/close_short 视为平仓事件。
      盈亏计算：
        long 平仓盈亏 = 出场价 - 入场价
        short 平仓盈亏 = 入场价 - 出场价
    """
    try:
        history = web_data.get('trade_history', [])
        if not history:
            web_data['performance']['total_trades'] = 0
            web_data['performance']['win_rate'] = 0.0
            return

        total = 0
        wins = 0
        current_open = None  # {'side': 'long'|'short', 'entry_price': float, 'amount': float}

        for rec in history:
            action = rec.get('action') or ''
            price = to_float(rec.get('price'), None)
            amount = to_float(rec.get('amount'), None)

            if action == 'open_long':
                if current_open is None:
                    current_open = {'side': 'long', 'entry_price': price, 'amount': amount}
                elif current_open.get('side') == 'short' and price is not None and current_open.get('entry_price') is not None and current_open.get('amount'):
                    # 平空仓：入场价 - 出场价
                    pnl = (current_open['entry_price'] - price) * current_open['amount']
                    total += 1
                    if pnl >= 0:
                        wins += 1
                    # 反转后开多
                    current_open = {'side': 'long', 'entry_price': price, 'amount': amount}
                else:
                    # 同向重复开仓记录，忽略
                    pass
            elif action == 'open_short':
                if current_open is None:
                    current_open = {'side': 'short', 'entry_price': price, 'amount': amount}
                elif current_open.get('side') == 'long' and price is not None and current_open.get('entry_price') is not None and current_open.get('amount'):
                    # 平多仓：出场价 - 入场价
                    pnl = (price - current_open['entry_price']) * current_open['amount']
                    total += 1
                    if pnl >= 0:
                        wins += 1
                    # 反转后开空
                    current_open = {'side': 'short', 'entry_price': price, 'amount': amount}
                else:
                    # 同向重复开仓记录，忽略
                    pass
            elif action == 'close_long':
                # 仅当当前持仓为long时有效
                if current_open and current_open.get('side') == 'long' and price is not None and current_open.get('entry_price') is not None and current_open.get('amount'):
                    pnl = (price - current_open['entry_price']) * current_open['amount']
                    total += 1
                    if pnl >= 0:
                        wins += 1
                    current_open = None
            elif action == 'close_short':
                # 仅当当前持仓为short时有效
                if current_open and current_open.get('side') == 'short' and price is not None and current_open.get('entry_price') is not None and current_open.get('amount'):
                    pnl = (current_open['entry_price'] - price) * current_open['amount']
                    total += 1
                    if pnl >= 0:
                        wins += 1
                    current_open = None
            else:
                # HOLD或未知动作，忽略
                pass

        web_data['performance']['total_trades'] = total
        web_data['performance']['win_rate'] = (wins / total * 100.0) if total > 0 else 0.0
    except Exception as e:
        print(f"计算胜率失败: {e}")
        # 避免前端显示空
        web_data['performance']['total_trades'] = web_data['performance'].get('total_trades', 0) or 0
        web_data['performance']['win_rate'] = web_data['performance'].get('win_rate', 0.0) or 0.0


def check_stop_take_profit(current_price):
    """检查最近一次开仓是否触发止损/止盈，触发则记录平仓事件并更新统计。
    仅在模拟/测试模式下执行自动平仓。
    """
    try:
        if not (os.getenv('PAPER_TRADING', 'true').lower() == 'true' or TRADE_CONFIG.get('test_mode', False)):
            return False

        last = get_last_open_trade()
        if not last or last.get('action') not in ('open_long', 'open_short'):
            return False

        side = 'long' if last['action'] == 'open_long' else 'short'
        sl = to_float(last.get('stop_loss'), None)
        tp = to_float(last.get('take_profit'), None)
        entry = to_float(last.get('price'), None)
        amount = to_float(last.get('amount'), None)
        price = to_float(current_price, None)

        if None in (sl, tp, entry, amount, price):
            return False

        triggered = None
        close_action = None
        close_signal = None
        if side == 'long':
            if price <= sl:
                triggered = '止损触发'
                close_action = 'close_long'
                close_signal = 'SELL'
            elif price >= tp:
                triggered = '止盈触发'
                close_action = 'close_long'
                close_signal = 'SELL'
        else:  # short
            if price >= sl:
                triggered = '止损触发'
                close_action = 'close_short'
                close_signal = 'BUY'
            elif price <= tp:
                triggered = '止盈触发'
                close_action = 'close_short'
                close_signal = 'BUY'

        if not triggered:
            return False

        # 记录到数据库
        signal_data = {
            'signal': close_signal,
            'confidence': 'HIGH',
            'reason': triggered,
            'stop_loss': sl,
            'take_profit': tp
        }
        price_data = {
            'price': price,
            'symbol': TRADE_CONFIG['symbol'],
            'timeframe': TRADE_CONFIG['timeframe'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        try:
            record_trade(signal_data, price_data, close_action, amount)
        except Exception as e_db:
            print(f"记录平仓到数据库失败: {e_db}")

        # 记录到内存历史
        web_data['trade_history'].append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': TRADE_CONFIG['symbol'],
            'timeframe': TRADE_CONFIG['timeframe'],
            'signal': close_signal,
            'action': close_action,
            'amount': amount,
            'price': price,
            'stop_loss': sl,
            'take_profit': tp,
            'confidence': 'HIGH',
            'reason': triggered
        })
        if len(web_data['trade_history']) > MEMORY_CONFIG['trade_history_limit']:
            web_data['trade_history'].pop(0)

        # 更新胜率统计
        try:
            compute_win_rate_from_history()
        except Exception as e_stats:
            print(f"更新胜率统计失败: {e_stats}")

        # 清除纸上持仓（视为已平仓）
        web_data['current_position'] = None
        print(f"✅ {triggered}，已执行{close_action} @ ${price:,.2f}")
        return True
    except Exception as e:
        print(f"检查止盈止损失败: {e}")
        return False


def test_ai_connection():
    """测试AI模型连接状态"""
    global web_data
    
    if not _OPENAI_AVAILABLE or ai_client is None:
        web_data['ai_model_info']['status'] = 'disabled'
        web_data['ai_model_info']['last_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        web_data['ai_model_info']['error_message'] = 'OpenAI模块不可用'
        print("⚠️ AI功能已禁用，跳过连接测试")
        return False
    
    try:
        print(f"🔍 测试 {AI_PROVIDER.upper()} 连接...")
        response = ai_client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "user", "content": "Hello"}
            ],
            max_tokens=10,
            timeout=10.0
        )
        
        if response and response.choices:
            web_data['ai_model_info']['status'] = 'connected'
            web_data['ai_model_info']['last_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            web_data['ai_model_info']['error_message'] = None
            print(f"✓ {AI_PROVIDER.upper()} 连接正常")
            return True
        else:
            web_data['ai_model_info']['status'] = 'error'
            web_data['ai_model_info']['last_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            web_data['ai_model_info']['error_message'] = '响应为空'
            print(f"❌ {AI_PROVIDER.upper()} 连接失败: 响应为空")
            return False
            
    except Exception as e:
        web_data['ai_model_info']['status'] = 'error'
        web_data['ai_model_info']['last_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        web_data['ai_model_info']['error_message'] = str(e)
        print(f"❌ {AI_PROVIDER.upper()} 连接失败: {e}")
        return False


def create_fallback_signal(price_data):
    """创建备用交易信号"""
    return {
        "signal": "HOLD",
        "reason": "因技术分析暂时不可用，采取保守策略",
        "stop_loss": price_data['price'] * 0.98,  # -2%
        "take_profit": price_data['price'] * 1.02,  # +2%
        "confidence": "LOW",
        "is_fallback": True
    }


def should_execute_trade(signal_data, current_position):
    """执行门槛判断：冷却时间、最小信心、首次确认。
    - HOLD 信号不执行
    - 低于最小信心阈值不执行
    - 距离最近开仓未超过冷却期不执行
    - 首次建仓需近3次里至少2次相同信号
    """
    try:
        signal = (signal_data.get('signal') or 'HOLD').upper()
        confidence = (signal_data.get('confidence') or 'LOW').upper()

        if signal == 'HOLD':
            return False

        # 最小信心阈值
        lvl = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
        min_conf = (TRADE_CONFIG.get('min_confidence_for_trade', 'MEDIUM') or 'MEDIUM').upper()
        if lvl.get(confidence, 0) < lvl.get(min_conf, 1):
            print(f"🚫 信心不足：{confidence} < {min_conf}")
            return False

        # 信号冷却时间（按最近一次开仓时间）
        cooldown_min = int(TRADE_CONFIG.get('signal_cooldown_minutes', 0) or 0)
        if cooldown_min > 0:
            last_open_dt = None
            for t in reversed(web_data.get('trade_history', [])):
                if t.get('action') in ('open_long', 'open_short'):
                    ts = t.get('timestamp')
                    try:
                        last_open_dt = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
                    except Exception:
                        last_open_dt = None
                    break
            if last_open_dt:
                if datetime.now() - last_open_dt < timedelta(minutes=cooldown_min):
                    print(f"⏱️ 冷却中：距上次开仓未满{cooldown_min}分钟")
                    return False

        # 首次建仓确认：最近3次中至少2次同向
        if TRADE_CONFIG.get('require_signal_confirmation', False):
            if not current_position and signal in ('BUY', 'SELL'):
                last_three = [s.get('signal') for s in signal_history[-3:]]
                same_count = last_three.count(signal)
                if same_count < 2:
                    print("🧯 首次建仓确认未满足：近3次里同向不足2次")
                    return False

        return True
    except Exception as e:
        print(f"执行门槛判断异常：{e}")
        return True  # 失败时不阻断，避免影响主流程


def analyze_with_deepseek(price_data):
    """使用DeepSeek分析市场并生成交易信号（增强版）"""

    # 生成技术分析文本
    technical_analysis = generate_technical_analysis_text(price_data)

    # 构建K线数据文本
    kline_text = f"【最近5根{TRADE_CONFIG['timeframe']}K线数据】\n"
    for i, kline in enumerate(price_data['kline_data'][-5:]):
        trend = "阳线" if kline['close'] > kline['open'] else "阴线"
        change = ((kline['close'] - kline['open']) / kline['open']) * 100
        kline_text += f"K线{i + 1}: {trend} 开盘:{kline['open']:.2f} 收盘:{kline['close']:.2f} 涨跌:{change:+.2f}%\n"

    # 添加上次交易信号
    signal_text = ""
    if signal_history:
        last_signal = signal_history[-1]
        signal_text = f"\n【上次交易信号】\n信号: {last_signal.get('signal', 'N/A')}\n信心: {last_signal.get('confidence', 'N/A')}"

    # 获取情绪数据
    sentiment_data = get_sentiment_indicators()
    # 简化情绪文本（多了没用）
    if sentiment_data:
        sign = '+' if sentiment_data['net_sentiment'] >= 0 else ''
        sentiment_text = f"【市场情绪】乐观{sentiment_data['positive_ratio']:.1%} 悲观{sentiment_data['negative_ratio']:.1%} 净值{sign}{sentiment_data['net_sentiment']:.3f}"
    else:
        sentiment_text = "【市场情绪】数据暂不可用"

    print(sentiment_text)

    # 添加当前持仓信息
    current_pos = get_current_position()
    position_text = "无持仓" if not current_pos else f"{current_pos['side']}仓, 数量: {current_pos['size']}, 盈亏: {current_pos['unrealized_pnl']:.2f}USDT"
    pnl_text = f", 持仓盈亏: {current_pos['unrealized_pnl']:.2f} USDT" if current_pos else ""

    # 使用结构化Prompt覆盖
    last_signal = signal_history[-1] if signal_history else None
    prompt = build_ai_prompt(price_data, last_signal=last_signal, sentiment_data=sentiment_data, current_pos=current_pos)

    # 检查AI是否可用
    if not _OPENAI_AVAILABLE or ai_client is None:
        print("⚠️ AI功能不可用，返回默认HOLD信号")
        fallback_decision = {
            'signal': 'HOLD',
            'reason': 'AI功能不可用，保持当前状态',
            'confidence': 'LOW',
            'stop_loss': None,
            'take_profit': None,
            'strategy_tag': 'fallback',
            'time_horizon': 'short',
            'risk_budget': 0.01
        }
        
        # 更新AI状态
        web_data['ai_model_info']['status'] = 'disabled'
        web_data['ai_model_info']['last_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        web_data['ai_model_info']['error_message'] = 'OpenAI模块不可用'
        
        return fallback_decision

    try:
        print(f"⏳ 正在调用{AI_PROVIDER.upper()} API ({AI_MODEL})...")
        response = ai_client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system",
                 "content": (
                     "你是专业量化交易AI。严格依据提供数据进行分析，"
                     "只输出一个JSON对象（不含任何额外文字），"
                     "键包括signal、reason、stop_loss、take_profit、confidence、strategy_tag、time_horizon、risk_budget。"
                     "遵守止损/止盈方向一致性与防频繁交易的原则。"
                 )},
                {"role": "user", "content": prompt}
            ],
            stream=False,
            temperature=0.1,
            timeout=30.0  # 30秒超时
        )
        print("✓ API调用成功")
        
        # 更新AI连接状态
        web_data['ai_model_info']['status'] = 'connected'
        web_data['ai_model_info']['last_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        web_data['ai_model_info']['error_message'] = None

        # 检查响应
        if not response or not response.choices:
            print(f"❌ {AI_PROVIDER.upper()}返回空响应")
            web_data['ai_model_info']['status'] = 'error'
            web_data['ai_model_info']['error_message'] = '响应为空'
            return create_fallback_signal(price_data)
        
        # 安全解析JSON
        result = response.choices[0].message.content
        if not result:
            print(f"❌ {AI_PROVIDER.upper()}返回空内容")
            return create_fallback_signal(price_data)
            
        print(f"\n{'='*60}")
        print(f"{AI_PROVIDER.upper()}原始回复:")
        print(result)
        print(f"{'='*60}\n")

        # 提取JSON部分
        start_idx = result.find('{')
        end_idx = result.rfind('}') + 1

        if start_idx != -1 and end_idx != 0:
            json_str = result[start_idx:end_idx]
            signal_data = safe_json_parse(json_str)

            if signal_data is None:
                print("⚠️ JSON解析失败，使用备用信号")
                signal_data = create_fallback_signal(price_data)
            else:
                print(f"✓ 成功解析AI决策: {signal_data.get('signal')} - {signal_data.get('confidence')}")
        else:
            print("⚠️ 未找到JSON格式，使用备用信号")
            signal_data = create_fallback_signal(price_data)

        # 验证必需字段
        required_fields = ['signal', 'reason', 'stop_loss', 'take_profit', 'confidence']
        if not all(field in signal_data for field in required_fields):
            missing = [f for f in required_fields if f not in signal_data]
            print(f"⚠️ 缺少必需字段: {missing}，使用备用信号")
            signal_data = create_fallback_signal(price_data)

        # 保存信号到历史记录
        signal_data['timestamp'] = price_data['timestamp']
        signal_history.append(signal_data)
        if len(signal_history) > MEMORY_CONFIG['signal_history_limit']:
            signal_history.pop(0)

        # 信号统计
        signal_count = len([s for s in signal_history if s.get('signal') == signal_data['signal']])
        total_signals = len(signal_history)
        print(f"信号统计: {signal_data['signal']} (最近{total_signals}次中出现{signal_count}次)")

        # 信号连续性检查
        if len(signal_history) >= 3:
            last_three = [s['signal'] for s in signal_history[-3:]]
            if len(set(last_three)) == 1:
                print(f"⚠️ 注意：连续3次{signal_data['signal']}信号")

        return signal_data

    except Exception as e:
        print(f"{AI_PROVIDER.upper()}分析失败: {e}")
        # 更新AI连接状态
        web_data['ai_model_info']['status'] = 'error'
        web_data['ai_model_info']['last_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        web_data['ai_model_info']['error_message'] = str(e)
        return create_fallback_signal(price_data)


def execute_trade(signal_data, price_data):
    """执行交易 - Binance FAPI 版本（修复保证金检查）"""
    global position, web_data

    current_position = get_current_position()
    # 执行门槛：冷却、最小信心、首次确认
    if not should_execute_trade(signal_data, current_position):
        print("⏸ 信号未达执行条件（冷却/信心/确认），跳过下单")
        return

    # 🔴 紧急修复：防止频繁反转
    if current_position and signal_data['signal'] != 'HOLD':
        current_side = current_position['side']
        # 修正：正确处理HOLD情况
        if signal_data['signal'] == 'BUY':
            new_side = 'long'
        elif signal_data['signal'] == 'SELL':
            new_side = 'short'
        else:  # HOLD
            new_side = None

        # 如果只是方向反转，需要高信心才执行
        if new_side != current_side:
            if signal_data['confidence'] != 'HIGH':
                print(f"🔒 非高信心反转信号，保持现有{current_side}仓")
                return

            # 检查最近信号历史，避免频繁反转
            if len(signal_history) >= 2:
                last_signals = [s['signal'] for s in signal_history[-2:]]
                if signal_data['signal'] in last_signals:
                    print(f"🔒 近期已出现{signal_data['signal']}信号，避免频繁反转")
                    return

    # 保障数值字段为浮点数以避免格式化异常
    _stop_loss = to_float(signal_data.get('stop_loss'), price_data.get('price', 0) * 0.98)
    _take_profit = to_float(signal_data.get('take_profit'), price_data.get('price', 0) * 1.02)

    print(f"交易信号: {signal_data['signal']}")
    print(f"信心程度: {signal_data['confidence']}")
    print(f"理由: {signal_data['reason']}")
    print(f"止损: ${_stop_loss:,.2f}")
    print(f"止盈: ${_take_profit:,.2f}")

    # 模拟交易：不执行真实下单，只记录数据库
    if os.getenv('PAPER_TRADING', 'true').lower() == 'true' or TRADE_CONFIG.get('test_mode', False):
        try:
            # 若存在持仓且新信号与当前方向相反，先记录平仓
            if current_position and signal_data['signal'] in ('BUY', 'SELL'):
                curr_side = current_position.get('side')
                if curr_side in ('long', 'short'):
                    close_action = 'close_long' if curr_side == 'long' else 'close_short'
                    close_signal = 'SELL' if curr_side == 'long' else 'BUY'
                    close_amount = to_float(current_position.get('size'), TRADE_CONFIG['amount'])
                    close_sd = {
                        'signal': close_signal,
                        'confidence': 'HIGH',
                        'reason': 'reversal_close',
                        'stop_loss': _stop_loss,
                        'take_profit': _take_profit
                    }
                    record_trade(close_sd, price_data, close_action, close_amount)
                    web_data['trade_history'].append({
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'symbol': TRADE_CONFIG['symbol'],
                        'timeframe': TRADE_CONFIG['timeframe'],
                        'signal': close_signal,
                        'action': close_action,
                        'amount': close_amount,
                        'price': price_data.get('price', 0),
                        'stop_loss': _stop_loss,
                        'take_profit': _take_profit,
                        'confidence': 'HIGH',
                        'reason': 'reversal_close'
                    })

            # 记录开仓（BUY→open_long，SELL→open_short）
            action = {'BUY': 'open_long', 'SELL': 'open_short'}.get(signal_data['signal'], 'hold')
            # 写入数据库前也保证数值字段为浮点数
            signal_data['stop_loss'] = _stop_loss
            signal_data['take_profit'] = _take_profit
            record_trade(signal_data, price_data, action, TRADE_CONFIG['amount'])
            # 同步到Web内存，便于前端展示
            web_data['trade_history'].append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': TRADE_CONFIG['symbol'],
                'timeframe': TRADE_CONFIG['timeframe'],
                'signal': signal_data['signal'],
                'action': action,
                'amount': TRADE_CONFIG['amount'],
                'price': price_data.get('price', 0),
                'stop_loss': _stop_loss,
                'take_profit': _take_profit,
                'confidence': signal_data['confidence'],
                'reason': signal_data['reason']
            })

            # 从数据库更新胜率与交易次数
            try:
                stats = compute_win_rate_from_db()
                web_data['performance']['win_rate'] = stats.get('win_rate', 0)
                web_data['performance']['total_trades'] = stats.get('total_trades', 0)
                web_data['performance']['total_profit'] = stats.get('total_profit', 0.0)
            except Exception as e_stats:
                print(f"更新胜率统计失败: {e_stats}")
            # 更新纸上持仓以便前端显示
            try:
                web_data['current_position'] = compute_paper_position(price_data.get('price'))
            except Exception as e_pos:
                print(f"更新纸上持仓失败: {e_pos}")
            print("✅ 模拟交易记录完成（未执行真实下单）")
        except Exception as e:
            print(f"❌ 模拟交易记录失败: {e}")
        return
    print(f"当前持仓: {current_position}")

    # 风险管理：低信心信号不执行
    if signal_data['confidence'] == 'LOW' and not TRADE_CONFIG['test_mode']:
        print("⚠️ 低信心信号，跳过执行")
        return

    if TRADE_CONFIG['test_mode']:
        print("测试模式 - 仅模拟交易")
        return

    try:
        # 获取账户余额
        balance = safe_fetch_balance()
        usdt_balance = balance['USDT']['free']
        required_margin = price_data['price'] * TRADE_CONFIG['amount'] / TRADE_CONFIG['leverage']

        if required_margin > usdt_balance * 0.8:  # 使用不超过80%的余额
            print(f"⚠️ 保证金不足，跳过交易。需要: {required_margin:.2f} USDT, 可用: {usdt_balance:.2f} USDT")
            return

        # 执行交易逻辑（Binance Futures，不使用OKX特有的 tag 参数）
        if signal_data['signal'] == 'BUY':
            if current_position and current_position['side'] == 'short':
                print("平空仓并开多仓...")
                # 平空仓
                exchange.create_market_order(
                    TRADE_CONFIG['symbol'],
                    'buy',
                    current_position['size'],
                    params={'reduceOnly': True}
                )
                time.sleep(1)
                # 开多仓
                exchange.create_market_order(
                    TRADE_CONFIG['symbol'],
                    'buy',
                    TRADE_CONFIG['amount']
                )
            elif current_position and current_position['side'] == 'long':
                print("已有多头持仓，保持现状")
            else:
                # 无持仓时开多仓
                print("开多仓...")
                exchange.create_market_order(
                    TRADE_CONFIG['symbol'],
                    'buy',
                    TRADE_CONFIG['amount']
                )

        elif signal_data['signal'] == 'SELL':
            if current_position and current_position['side'] == 'long':
                print("平多仓并开空仓...")
                # 平多仓
                exchange.create_market_order(
                    TRADE_CONFIG['symbol'],
                    'sell',
                    current_position['size'],
                    params={'reduceOnly': True}
                )
                time.sleep(1)
                # 开空仓
                exchange.create_market_order(
                    TRADE_CONFIG['symbol'],
                    'sell',
                    TRADE_CONFIG['amount']
                )
            elif current_position and current_position['side'] == 'short':
                print("已有空头持仓，保持现状")
            else:
                # 无持仓时开空仓
                print("开空仓...")
                exchange.create_market_order(
                    TRADE_CONFIG['symbol'],
                    'sell',
                    TRADE_CONFIG['amount']
                )

        print("订单执行成功")
        time.sleep(2)
        position = get_current_position()
        print(f"更新后持仓: {position}")
        
        # 记录交易历史
        trade_record = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'signal': signal_data['signal'],
            'price': price_data['price'],
            'amount': TRADE_CONFIG['amount'],
            'confidence': signal_data['confidence'],
            'reason': signal_data['reason']
        }
        web_data['trade_history'].append(trade_record)
        if len(web_data['trade_history']) > MEMORY_CONFIG['trade_history_limit']:  # 内存优化：保留最近50条
            web_data['trade_history'].pop(0)
        # 更新胜率统计（基于交易方向反转视为平仓）
        try:
            compute_win_rate_from_history()
        except Exception as e_stats:
            print(f"更新胜率统计失败: {e_stats}")

    except Exception as e:
        print(f"订单执行失败: {e}")
        import traceback
        traceback.print_exc()


def analyze_with_deepseek_with_retry(price_data, max_retries=2):
    """带重试的DeepSeek分析"""
    for attempt in range(max_retries):
        try:
            signal_data = analyze_with_deepseek(price_data)
            if signal_data and not signal_data.get('is_fallback', False):
                return signal_data

            print(f"第{attempt + 1}次尝试失败，进行重试...")
            time.sleep(2)

        except Exception as e:
            print(f"第{attempt + 1}次尝试异常: {e}")
            import traceback
            traceback.print_exc()
            if attempt == max_retries - 1:
                return create_fallback_signal(price_data)
            time.sleep(2)

    return create_fallback_signal(price_data)


def wait_for_next_period():
    """等待到下一个15分钟整点"""
    now = datetime.now()
    current_minute = now.minute
    current_second = now.second

    # 计算下一个整点时间（00, 15, 30, 45分钟）
    next_period_minute = ((current_minute // 15) + 1) * 15
    if next_period_minute == 60:
        next_period_minute = 0

    # 计算需要等待的总秒数
    if next_period_minute > current_minute:
        minutes_to_wait = next_period_minute - current_minute
    else:
        minutes_to_wait = 60 - current_minute + next_period_minute

    seconds_to_wait = minutes_to_wait * 60 - current_second

    # 显示友好的等待时间
    display_minutes = minutes_to_wait - 1 if current_second > 0 else minutes_to_wait
    display_seconds = 60 - current_second if current_second > 0 else 0

    if display_minutes > 0:
        print(f"🕒 等待 {display_minutes} 分 {display_seconds} 秒到整点...")
    else:
        print(f"🕒 等待 {display_seconds} 秒到整点...")

    return seconds_to_wait


def trading_bot():
    # 首次运行不等待，之后每次等待到下一个整点
    global has_run_once
    wait_seconds = 0 if not has_run_once else wait_for_next_period()
    if wait_seconds > 0:
        time.sleep(wait_seconds)
    has_run_once = True

    """主交易机器人函数"""
    global web_data, initial_balance
    
    print("\n" + "=" * 60)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. 获取增强版K线数据
    price_data = get_btc_ohlcv_enhanced()
    if not price_data:
        return

    print(f"BTC当前价格: ${price_data['price']:,.2f}")
    print(f"数据周期: {TRADE_CONFIG['timeframe']}")
    print(f"价格变化: {price_data['price_change']:+.2f}%")

    # 2. 使用DeepSeek分析（带重试）
    signal_data = analyze_with_deepseek_with_retry(price_data)

    if signal_data.get('is_fallback', False):
        print("⚠️ 使用备用交易信号")

    # 3. 更新Web数据
    try:
        balance = safe_fetch_balance()
        current_equity = balance['USDT']['total']
        
        # 设置初始余额
        if initial_balance is None:
            initial_balance = current_equity
        
        # 计算实时总盈亏
        total_profit = current_equity - initial_balance
        
        # 获取当前持仓的未实现盈亏
        current_position = get_current_position()
        unrealized_pnl = current_position.get('unrealized_pnl', 0) if current_position else 0
        
        # 计算实际可用余额（考虑未实现盈亏）
        adjusted_balance = balance['USDT']['free'] + unrealized_pnl
        adjusted_equity = current_equity + unrealized_pnl
        
        web_data['account_info'] = {
            'usdt_balance': balance['USDT']['free'],
            'total_equity': current_equity,
            'adjusted_balance': adjusted_balance,  # 调整后的可用余额
            'adjusted_equity': adjusted_equity,    # 调整后的总权益
            'total_profit': total_profit,          # 总盈亏
            'unrealized_pnl': unrealized_pnl       # 未实现盈亏
        }
        
        # 记录收益曲线数据
        current_position = get_current_position()
        unrealized_pnl = current_position.get('unrealized_pnl', 0) if current_position else 0
        total_profit = current_equity - initial_balance
        profit_rate = (total_profit / initial_balance * 100) if initial_balance > 0 else 0
        
        profit_point = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'equity': current_equity,
            'profit': total_profit,
            'profit_rate': profit_rate,
            'unrealized_pnl': unrealized_pnl
        }
        web_data['profit_curve'].append(profit_point)
        
        # 只保留最近200个数据点（约50小时）
        if len(web_data['profit_curve']) > MEMORY_CONFIG['profit_curve_limit']:
            web_data['profit_curve'].pop(0)
            
    except Exception as e:
        print(f"更新余额失败: {e}")
        # 模拟模式下：使用默认权益计算收益曲线，并回退持仓
        current_equity = 10000.0
        
        # 设置初始余额（首次）
        if initial_balance is None:
            initial_balance = current_equity
        
        # 计算实时总盈亏
        total_profit = current_equity - initial_balance
        
        # 获取当前持仓的未实现盈亏
        pos = None
        try:
            pos = compute_paper_position(price_data['price'])
        except Exception:
            pos = None
        web_data['current_position'] = pos
        
        unrealized_pnl = pos.get('unrealized_pnl', 0) if pos else 0
        
        # 计算实际可用余额（考虑未实现盈亏）
        adjusted_balance = 10000.0 + unrealized_pnl
        adjusted_equity = current_equity + unrealized_pnl
        
        web_data['account_info'] = {
            'usdt_balance': 10000.0,
            'total_equity': current_equity,
            'adjusted_balance': adjusted_balance,  # 调整后的可用余额
            'adjusted_equity': adjusted_equity,    # 调整后的总权益
            'total_profit': total_profit,          # 总盈亏
            'unrealized_pnl': unrealized_pnl       # 未实现盈亏
        }
        # 记录收益曲线（基于模拟权益与未实现盈亏）
        unrealized_pnl = pos.get('unrealized_pnl', 0) if pos else 0
        total_profit = web_data['account_info']['total_equity'] - initial_balance
        profit_rate = (total_profit / initial_balance * 100) if initial_balance > 0 else 0
        profit_point = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'equity': web_data['account_info']['total_equity'],
            'profit': total_profit,
            'profit_rate': profit_rate,
            'unrealized_pnl': unrealized_pnl
        }
        web_data['profit_curve'].append(profit_point)
        if len(web_data['profit_curve']) > MEMORY_CONFIG['profit_curve_limit']:
            web_data['profit_curve'].pop(0)
    
    web_data['current_price'] = price_data['price']
    # 在更新持仓前检查止盈/止损是否触发平仓
    try:
        check_stop_take_profit(price_data['price'])
    except Exception:
        pass
    # 优先真实持仓，失败回退纸上推导
    cur_pos = None
    try:
        cur_pos = get_current_position()
    except Exception:
        cur_pos = None
    if not cur_pos:
        try:
            cur_pos = compute_paper_position(price_data['price'])
        except Exception:
            cur_pos = None
    web_data['current_position'] = cur_pos
    web_data['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 保存K线数据
    web_data['kline_data'] = price_data['kline_data']
    # 保存数据源标记与周期
    web_data['data_source'] = price_data.get('data_source', 'unknown')
    web_data['is_fallback_data'] = price_data.get('is_fallback_data', False)
    web_data['timeframe'] = TRADE_CONFIG['timeframe']

    # 打印数据源标记，便于诊断
    try:
        print(f"数据源标记: {web_data.get('data_source', 'unknown')}, fallback: {web_data.get('is_fallback_data', False)}")
    except Exception:
        pass
    
    # 保障数值字段为浮点数，避免前端toFixed报错
    stop_loss_val = to_float(signal_data.get('stop_loss'), price_data['price'] * 0.98)
    take_profit_val = to_float(signal_data.get('take_profit'), price_data['price'] * 1.02)

    # 保存AI决策
    ai_decision = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'signal': signal_data['signal'],
        'confidence': signal_data['confidence'],
        'reason': signal_data['reason'],
        'stop_loss': stop_loss_val,
        'take_profit': take_profit_val,
        'price': price_data['price']
    }
    web_data['ai_decisions'].append(ai_decision)
    if len(web_data['ai_decisions']) > MEMORY_CONFIG['ai_decisions_limit']:  # 内存优化：保留最近30条
            web_data['ai_decisions'].pop(0)
    
    # 更新性能统计
    if web_data['current_position']:
        web_data['performance']['total_profit'] = web_data['current_position'].get('unrealized_pnl', 0)

    # 4. 执行交易
    execute_trade(signal_data, price_data)

    # 5. 更新胜率与交易次数统计（基于反转视为平仓）
    try:
        compute_win_rate_from_history()
    except Exception as e_stats:
        print(f"更新胜率统计失败: {e_stats}")



def main():
    """主函数"""
    print("BTC/USDT Binance FAPI 自动交易机器人启动成功！")
    print(f"AI模型: {AI_PROVIDER.upper()} ({AI_MODEL})")
    print("融合技术指标策略 + Binance USDT-M 永续接口")

    if TRADE_CONFIG['test_mode']:
        print("当前为模拟模式，不会真实下单")
    else:
        print("实盘交易模式，请谨慎操作！")

    print(f"交易周期: {TRADE_CONFIG['timeframe']}")
    print("已启用完整技术指标分析和持仓跟踪功能")

    # 设置交易所
    if not setup_exchange():
        print("交易所初始化失败，将继续进入模拟交易，仅加载行情与AI决策")

    print("执行频率: 每15分钟整点执行")

    # 循环执行（不使用schedule）
    while True:
        trading_bot()  # 函数内部会自己等待整点

        # 执行完后等待一段时间再检查（避免频繁循环）
        time.sleep(60)  # 每分钟检查一次


if __name__ == "__main__":
    main()