#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试交易记录 - 修复版本
使用正确的record_trade参数格式
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import requests

def get_real_btc_price():
    """获取真实的BTC价格"""
    try:
        response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=5)
        data = response.json()
        return float(data['price'])
    except:
        return 65000.0  # 默认价格

def clear_existing_trades():
    """清空现有交易记录"""
    try:
        from paper_trading import _get_db_conn
        
        conn = _get_db_conn()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM trades")
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print("🗑️ 已清空现有交易记录")
        return True
        
    except Exception as e:
        print(f"❌ 清空交易记录失败: {e}")
        return False

def create_test_trades():
    """创建测试交易记录"""
    try:
        from paper_trading import record_trade
        
        # 获取当前BTC价格
        current_price = get_real_btc_price()
        print(f"💰 当前BTC价格: ${current_price:,.2f}")
        
        # 创建测试交易数据 - 模拟66.7%胜率（2胜1负）
        base_time = datetime.now() - timedelta(days=7)
        
        trades = [
            # 第一笔交易 - 盈利 (开多 -> 平多)
            {
                'signal_data': {
                    'signal': 'BUY',
                    'confidence': 'HIGH',
                    'reason': '测试交易1-开多',
                    'stop_loss': current_price - 3000,
                    'take_profit': current_price - 1000
                },
                'price_data': {
                    'price': current_price - 2000,
                    'symbol': 'BTC/USDT',
                    'timeframe': '15m'
                },
                'action': 'open_long',
                'amount': 0.01
            },
            {
                'signal_data': {
                    'signal': 'SELL',
                    'confidence': 'HIGH',
                    'reason': '测试交易1-平多-盈利',
                    'stop_loss': None,
                    'take_profit': None
                },
                'price_data': {
                    'price': current_price - 1500,  # 盈利500
                    'symbol': 'BTC/USDT',
                    'timeframe': '15m'
                },
                'action': 'close_long',
                'amount': 0.01
            },
            
            # 第二笔交易 - 亏损 (开空 -> 平空)
            {
                'signal_data': {
                    'signal': 'SELL',
                    'confidence': 'MEDIUM',
                    'reason': '测试交易2-开空',
                    'stop_loss': current_price - 500,
                    'take_profit': current_price - 1500
                },
                'price_data': {
                    'price': current_price - 1000,
                    'symbol': 'BTC/USDT',
                    'timeframe': '15m'
                },
                'action': 'open_short',
                'amount': 0.01
            },
            {
                'signal_data': {
                    'signal': 'BUY',
                    'confidence': 'HIGH',
                    'reason': '测试交易2-平空-亏损',
                    'stop_loss': None,
                    'take_profit': None
                },
                'price_data': {
                    'price': current_price - 800,  # 亏损200
                    'symbol': 'BTC/USDT',
                    'timeframe': '15m'
                },
                'action': 'close_short',
                'amount': 0.01
            },
            
            # 第三笔交易 - 盈利 (开多 -> 平多)
            {
                'signal_data': {
                    'signal': 'BUY',
                    'confidence': 'HIGH',
                    'reason': '测试交易3-开多',
                    'stop_loss': current_price - 800,
                    'take_profit': current_price - 200
                },
                'price_data': {
                    'price': current_price - 500,
                    'symbol': 'BTC/USDT',
                    'timeframe': '15m'
                },
                'action': 'open_long',
                'amount': 0.01
            },
            {
                'signal_data': {
                    'signal': 'SELL',
                    'confidence': 'HIGH',
                    'reason': '测试交易3-平多-盈利',
                    'stop_loss': None,
                    'take_profit': None
                },
                'price_data': {
                    'price': current_price - 200,  # 盈利300
                    'symbol': 'BTC/USDT',
                    'timeframe': '15m'
                },
                'action': 'close_long',
                'amount': 0.01
            }
        ]
        
        print("🔧 创建测试交易记录...")
        
        for i, trade in enumerate(trades, 1):
            try:
                record_trade(
                    trade['signal_data'],
                    trade['price_data'],
                    trade['action'],
                    trade['amount']
                )
                print(f"✅ 交易{i}: {trade['action']} @ ${trade['price_data']['price']:,.2f}")
                
            except Exception as e:
                print(f"❌ 创建交易{i}失败: {e}")
                return False
        
        print("✅ 测试交易记录创建完成")
        return True
        
    except Exception as e:
        print(f"❌ 创建测试交易失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_win_rate():
    """验证胜率计算"""
    try:
        from paper_trading import compute_win_rate_from_db
        
        print("\n📊 验证胜率计算:")
        stats = compute_win_rate_from_db()
        
        print(f"   胜率: {stats.get('win_rate', 0)}%")
        print(f"   总交易次数: {stats.get('total_trades', 0)}")
        print(f"   总盈亏: ${stats.get('total_profit', 0):.2f}")
        
        expected_win_rate = 66.7  # 2胜1负
        actual_win_rate = stats.get('win_rate', 0)
        
        if abs(actual_win_rate - expected_win_rate) < 1:
            print("✅ 胜率计算正确")
            return True
        else:
            print(f"❌ 胜率计算错误，期望{expected_win_rate}%，实际{actual_win_rate}%")
            return False
            
    except Exception as e:
        print(f"❌ 胜率验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_web_data_sync():
    """检查web_data同步"""
    try:
        import deepseekok2
        
        print("\n🔍 检查web_data同步:")
        performance = deepseekok2.web_data.get('performance', {})
        
        print(f"   web_data胜率: {performance.get('win_rate', 'N/A')}")
        print(f"   web_data总交易: {performance.get('total_trades', 'N/A')}")
        print(f"   web_data总盈亏: ${performance.get('total_profit', 0):.2f}")
        
        return performance
        
    except Exception as e:
        print(f"❌ web_data检查失败: {e}")
        return None

def main():
    print("="*60)
    print("🧪 创建测试交易记录")
    print("="*60)
    
    try:
        # 加载环境变量
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ 环境变量加载成功")
        
        # 1. 清空现有记录
        if not clear_existing_trades():
            return
        
        # 2. 创建测试交易
        if not create_test_trades():
            print("❌ 测试数据创建失败")
            return
        
        # 3. 验证胜率计算
        if not verify_win_rate():
            print("❌ 胜率验证失败")
            return
        
        # 4. 检查web_data同步
        web_performance = check_web_data_sync()
        
        print("\n" + "="*60)
        print("📋 测试总结:")
        print("="*60)
        print("✅ 测试交易记录创建成功")
        print("✅ 胜率计算正确 (66.7%)")
        print("💡 现在可以重启web服务器并检查网页显示")
        print("="*60)
        
    except Exception as e:
        print(f"❌ 脚本执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()