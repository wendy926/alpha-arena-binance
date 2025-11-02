from flask import Flask, jsonify, render_template
from flask_cors import CORS
import threading
import sys
import os
import requests
from datetime import datetime

# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 导入主程序
import deepseekok2
from paper_trading import init_db, list_trades, compute_win_rate_from_db

# 明确指定模板和静态文件路径
app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))

# 配置Flask的JSON编码设置
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

CORS(app)

@app.route('/')
def index():
    """主页"""
    try:
        return render_template('index.html')
    except Exception as e:
        return f"<h1>模板加载错误</h1><p>{str(e)}</p><p>模板路径: {app.template_folder}</p>"

@app.route('/api/dashboard')
def get_dashboard_data():
    """获取仪表板数据"""
    try:
        # 实时更新账户信息
        try:
            balance = deepseekok2.safe_fetch_balance()
            current_equity = balance['USDT']['total']
            
            # 设置初始余额
            if deepseekok2.initial_balance is None:
                deepseekok2.initial_balance = current_equity
            
            # 实时保证持仓有值：优先尝试真实持仓，否则回退到纸上持仓
            pos = deepseekok2.web_data.get('current_position')
            if not pos:
                try:
                    pos = deepseekok2.get_current_position()
                except Exception:
                    pos = None
                if not pos:
                    try:
                        pos = deepseekok2.compute_paper_position(deepseekok2.web_data.get('current_price'))
                    except Exception:
                        pos = None
                deepseekok2.web_data['current_position'] = pos
            
            # 获取未实现盈亏
            unrealized_pnl = pos.get('unrealized_pnl', 0) if pos else 0
            
            # 计算历史已实现盈亏（从数据库获取）
            try:
                stats = compute_win_rate_from_db()
                historical_profit = stats.get('total_profit', 0.0)
            except Exception:
                historical_profit = 0.0
            
            # 计算总盈亏（历史交易盈亏 + 当前未实现盈亏）
            total_profit = historical_profit + unrealized_pnl
            
            # 计算调整后的余额和总权益（使用起始金额 + 总盈亏）
            initial_balance = 10000.0  # 默认起始金额
            adjusted_balance = initial_balance + total_profit
            adjusted_equity = current_equity + unrealized_pnl
            
            # 更新账户信息
            deepseekok2.web_data['account_info'] = {
                'usdt_balance': balance['USDT']['free'],
                'total_equity': current_equity,
                'adjusted_balance': adjusted_balance,
                'adjusted_equity': adjusted_equity,
                'historical_profit': historical_profit,  # 历史交易盈亏
                'total_profit': total_profit,  # 总盈亏（历史 + 未实现）
                'unrealized_pnl': unrealized_pnl  # 当前持仓未实现盈亏
            }
            
        except Exception as e:
            print(f"实时更新账户信息失败: {e}")
            # 如果账户信息为空，使用默认值
            if not deepseekok2.web_data.get('account_info'):
                deepseekok2.web_data['account_info'] = {
                    'usdt_balance': 10000.0,
                    'total_equity': 10000.0,
                    'adjusted_balance': 10000.0,
                    'adjusted_equity': 10000.0,
                    'total_profit': 0.0,
                    'unrealized_pnl': 0.0
                }

        # 计算胜率与交易次数（基于数据库记录）
        try:
            stats = compute_win_rate_from_db()
            deepseekok2.web_data['performance']['win_rate'] = stats.get('win_rate', 0.0)
            deepseekok2.web_data['performance']['total_trades'] = stats.get('total_trades', 0)
            # 注意：这里的total_profit是历史交易的累计盈亏，不要覆盖account_info中的实时总盈亏
            deepseekok2.web_data['performance']['historical_profit'] = stats.get('total_profit', 0.0)
            print(f"✅ 胜率计算成功: {stats.get('win_rate', 0.0)}%, 总交易: {stats.get('total_trades', 0)}, 历史盈亏: ${stats.get('total_profit', 0.0):.2f}")
                
        except Exception as e_stats:
            print(f"❌ 计算胜率失败: {e_stats}")
            import traceback
            traceback.print_exc()
            # 使用默认值
            deepseekok2.web_data['performance']['win_rate'] = 0.0
            deepseekok2.web_data['performance']['total_trades'] = 0
            deepseekok2.web_data['performance']['historical_profit'] = 0.0

        # 性能统计：保持account_info中的实时总盈亏不被覆盖
        # account_info['total_profit'] = 实时总盈亏（已实现 + 未实现）
        # performance['historical_profit'] = 历史交易累计盈亏（仅来自数据库记录）

        data = {
            'account_info': deepseekok2.web_data['account_info'],
            'current_position': deepseekok2.web_data['current_position'],
            'current_price': deepseekok2.web_data['current_price'],
            'last_update': deepseekok2.web_data['last_update'],
            'performance': deepseekok2.web_data['performance'],
            'config': {
                'symbol': deepseekok2.TRADE_CONFIG['symbol'],
                'leverage': deepseekok2.TRADE_CONFIG['leverage'],
                'timeframe': deepseekok2.TRADE_CONFIG['timeframe'],
                'test_mode': deepseekok2.TRADE_CONFIG['test_mode']
            }
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kline')
def get_kline_data():
    """获取K线数据"""
    try:
        return jsonify({
            'data_source': deepseekok2.web_data.get('data_source'),
            'is_fallback_data': deepseekok2.web_data.get('is_fallback_data', False),
            'timeframe': deepseekok2.web_data.get('timeframe', deepseekok2.TRADE_CONFIG['timeframe']),
            'kline_data': deepseekok2.web_data['kline_data']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades')
def get_trade_history():
    """获取交易历史"""
    try:
        # 优先从数据库返回最近交易列表
        trades = []
        try:
            trades = list_trades(limit=100)
        except Exception as e_db:
            print(f"读取数据库交易失败，回退到内存: {e_db}")
            trades = deepseekok2.web_data['trade_history']
        return jsonify(trades)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai_decisions')
def get_ai_decisions():
    """获取AI决策历史"""
    try:
        ai_decisions = deepseekok2.web_data.get('ai_decisions', [])
        
        # 确保返回的数据格式正确
        if not isinstance(ai_decisions, list):
            ai_decisions = []
        
        # 验证每个决策对象的完整性
        validated_decisions = []
        for decision in ai_decisions:
            if isinstance(decision, dict):
                # 确保必要字段存在
                validated_decision = {
                    'signal': decision.get('signal', 'HOLD'),
                    'confidence': decision.get('confidence', 'LOW'),
                    'reason': decision.get('reason', '暂无分析'),
                    'stop_loss': float(decision.get('stop_loss', 0)),
                    'take_profit': float(decision.get('take_profit', 0)),
                    'timestamp': decision.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                }
                validated_decisions.append(validated_decision)
        
        return jsonify(validated_decisions)
    except Exception as e:
        print(f"❌ AI决策API错误: {e}")
        import traceback
        traceback.print_exc()
        # 返回空数组而不是错误，避免前端JSON解析失败
        return jsonify([])

@app.route('/api/signals')
def get_signal_history():
    """获取信号历史统计"""
    try:
        signals = deepseekok2.signal_history
        
        # 统计信号分布
        signal_stats = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
        confidence_stats = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        
        for signal in signals:
            signal_type = signal.get('signal', 'HOLD')
            confidence = signal.get('confidence', 'LOW')
            signal_stats[signal_type] = signal_stats.get(signal_type, 0) + 1
            confidence_stats[confidence] = confidence_stats.get(confidence, 0) + 1
        
        return jsonify({
            'signal_stats': signal_stats,
            'confidence_stats': confidence_stats,
            'total_signals': len(signals),
            'recent_signals': signals[-10:] if signals else []
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profit_curve')
def get_profit_curve():
    """获取收益曲线数据"""
    try:
        return jsonify(deepseekok2.web_data['profit_curve'])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai_model_info')
def get_ai_model_info():
    """获取AI模型信息和连接状态"""
    try:
        return jsonify(deepseekok2.web_data['ai_model_info'])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test_ai')
def test_ai_connection():
    """手动测试AI连接"""
    try:
        result = deepseekok2.test_ai_connection()
        return jsonify({
            'success': result,
            'info': deepseekok2.web_data['ai_model_info']
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/health')
def get_health():
    """检查到交易所公共API的连通性"""
    def check(url, timeout=5):
        try:
            resp = requests.get(url, timeout=timeout)
            return {'reachable': True, 'status_code': resp.status_code}
        except Exception as e:
            return {'reachable': False, 'error': str(e)}

    results = {
        'okx_market': check('https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT-SWAP'),
        'binance_futures': check('https://fapi.binance.com/fapi/v1/ping'),
        'binance_spot': check('https://api.binance.com/api/v3/ping'),
        'last_check': deepseekok2.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    return jsonify(results)

def initialize_data():
    """启动时立即初始化一次数据"""
    try:
        print("正在初始化数据...")
        # 初始化模拟交易数据库
        init_db()
        
        # 测试AI连接
        print("\n🤖 测试AI模型连接...")
        deepseekok2.test_ai_connection()
        print()
        
        # 设置交易所（如果还没设置）
        try:
            # 测试一下exchange是否可用
            deepseekok2.safe_fetch_balance()
        except:
            # 如果不可用，进行设置（即使失败也继续加载公共行情数据）
            if not deepseekok2.setup_exchange():
                print("⚠️ 交易所初始化失败，继续加载公共行情数据（仅行情，不显示账户）")
        
        # 获取初始数据
        price_data = deepseekok2.get_btc_ohlcv_enhanced()
        if price_data:
            # 更新账户信息
            try:
                balance = deepseekok2.safe_fetch_balance()
                current_equity = balance['USDT']['total']
                
                # 设置初始余额
                if deepseekok2.initial_balance is None:
                    deepseekok2.initial_balance = current_equity
                
                # 获取当前持仓的未实现盈亏
                pos = None
                try:
                    pos = deepseekok2.get_current_position()
                except Exception:
                    pos = None
                if not pos:
                    try:
                        pos = deepseekok2.compute_paper_position(price_data['price'])
                    except Exception:
                        pos = None
                
                unrealized_pnl = pos.get('unrealized_pnl', 0) if pos else 0
                
                # 计算历史已实现盈亏（从数据库获取）
                try:
                    stats = compute_win_rate_from_db()
                    historical_profit = stats.get('total_profit', 0.0)
                except Exception:
                    historical_profit = 0.0
                
                # 计算总盈亏（历史交易盈亏 + 当前未实现盈亏）
                total_profit = historical_profit + unrealized_pnl
                
                # 计算调整后的余额和总权益（使用起始金额 + 总盈亏）
                initial_balance = 10000.0  # 默认起始金额
                adjusted_balance = initial_balance + total_profit
                adjusted_equity = current_equity + unrealized_pnl
                
                deepseekok2.web_data['account_info'] = {
                    'usdt_balance': balance['USDT']['free'],
                    'total_equity': current_equity,
                    'adjusted_balance': adjusted_balance,
                    'adjusted_equity': adjusted_equity,
                    'historical_profit': historical_profit,  # 历史交易盈亏
                    'total_profit': total_profit,            # 总盈亏（历史+未实现）
                    'unrealized_pnl': unrealized_pnl         # 未实现盈亏
                }
            except Exception as e:
                print(f"获取账户信息失败: {e}")
                # 模拟模式下设置默认可用余额为10000U
                current_equity = 10000.0
                
                # 设置初始余额
                if deepseekok2.initial_balance is None:
                    deepseekok2.initial_balance = current_equity
                
                # 获取当前持仓的未实现盈亏
                pos = None
                try:
                    pos = deepseekok2.compute_paper_position(price_data['price'])
                except Exception:
                    pos = None
                
                unrealized_pnl = pos.get('unrealized_pnl', 0) if pos else 0
                
                # 计算历史已实现盈亏（从数据库获取）
                try:
                    stats = compute_win_rate_from_db()
                    historical_profit = stats.get('total_profit', 0.0)
                except Exception:
                    historical_profit = 0.0
                
                # 计算总盈亏（历史交易盈亏 + 当前未实现盈亏）
                total_profit = historical_profit + unrealized_pnl
                
                # 计算调整后的余额和总权益（使用起始金额 + 总盈亏）
                initial_balance = 10000.0  # 默认起始金额
                adjusted_balance = initial_balance + total_profit
                adjusted_equity = current_equity + unrealized_pnl
                
                deepseekok2.web_data['account_info'] = {
                    'usdt_balance': 10000.0,
                    'total_equity': current_equity,
                    'adjusted_balance': adjusted_balance,
                    'adjusted_equity': adjusted_equity,
                    'historical_profit': historical_profit,  # 历史交易盈亏
                    'total_profit': total_profit,            # 总盈亏（历史+未实现）
                    'unrealized_pnl': unrealized_pnl         # 未实现盈亏
                }
            
            # 更新基础数据
            deepseekok2.web_data['current_price'] = price_data['price']
            # 优先尝试真实持仓；若无，则回退到纸上持仓
            pos = None
            try:
                pos = deepseekok2.get_current_position()
            except Exception:
                pos = None
            if not pos:
                try:
                    pos = deepseekok2.compute_paper_position(price_data['price'])
                except Exception:
                    pos = None
            deepseekok2.web_data['current_position'] = pos
            deepseekok2.web_data['kline_data'] = price_data['kline_data']
            deepseekok2.web_data['data_source'] = price_data.get('data_source')
            deepseekok2.web_data['is_fallback_data'] = price_data.get('is_fallback_data', False)
            deepseekok2.web_data['timeframe'] = price_data.get('timeframe', deepseekok2.TRADE_CONFIG['timeframe'])
            deepseekok2.web_data['last_update'] = deepseekok2.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 更新性能数据
            if deepseekok2.web_data['current_position']:
                deepseekok2.web_data['performance']['total_profit'] = deepseekok2.web_data['current_position'].get('unrealized_pnl', 0)
            
            print(f"✅ 初始化完成 - BTC价格: ${price_data['price']:,.2f}")
            print(f"✅ K线数据: {len(price_data['kline_data'])}条")
        else:
            print("⚠️ 获取K线数据失败")
            
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()

def run_trading_bot():
    """在独立线程中运行交易机器人"""
    deepseekok2.main()

if __name__ == '__main__':
    # 立即初始化数据（不等待15分钟）
    print("\n" + "="*60)
    print("🚀 启动BTC交易机器人Web监控...")
    print("="*60 + "\n")
    
    # 异步初始化，避免阻塞Web启动
    init_thread = threading.Thread(target=initialize_data, daemon=True)
    init_thread.start()
    
    # 启动交易机器人线程
    bot_thread = threading.Thread(target=run_trading_bot, daemon=True)
    bot_thread.start()
    
    # 启动Web服务器 - 优先使用环境变量PORT，否则使用默认8080
    PORT = int(os.environ.get('PORT', 8080))
    print("\n" + "="*60)
    print("🌐 Web管理界面启动成功！")
    print(f"📊 访问地址: http://localhost:{PORT}")
    print(f"📁 模板目录: {app.template_folder}")
    print(f"📁 静态目录: {app.static_folder}")
    print(f"📄 模板文件存在: {os.path.exists(os.path.join(app.template_folder, 'index.html'))}")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)

