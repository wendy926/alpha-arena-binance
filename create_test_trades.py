#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试交易记录来验证胜率计算
"""

import os
import sys
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_trades():
    """创建测试交易记录"""
    try:
        from paper_trading import record_trade, compute_win_rate_from_db
        
        print("🔧 创建测试交易记录...")
        
        # 基础时间
        base_time = datetime.now() - timedelta(days=7)
        
        # 创建一些测试交易（模拟66.7%胜率：2胜1负）
        test_trades = [
            # 第一笔交易 - 盈利
            {
                'timestamp': base_time.strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': 'BTC/USDT',
                'timeframe': '15m',
                'signal': 'BUY',
                'action': 'open_long',
                'amount': 0.01,
                'price': 45000.0,
                'stop_loss': 44000.0,
                'take_profit': 46000.0,
                'confidence': 'HIGH',
                'reason': 'AI分析：强烈看涨信号'
            },
            {
                'timestamp': (base_time + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': 'BTC/USDT',
                'timeframe': '15m',
                'signal': 'SELL',
                'action': 'close_long',
                'amount': 0.01,
                'price': 46500.0,  # 盈利
                'stop_loss': None,
                'take_profit': None,
                'confidence': 'HIGH',
                'reason': '达到止盈目标'
            },
            
            # 第二笔交易 - 盈利
            {
                'timestamp': (base_time + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': 'BTC/USDT',
                'timeframe': '15m',
                'signal': 'SELL',
                'action': 'open_short',
                'amount': 0.01,
                'price': 47000.0,
                'stop_loss': 48000.0,
                'take_profit': 46000.0,
                'confidence': 'MEDIUM',
                'reason': 'AI分析：看跌信号'
            },
            {
                'timestamp': (base_time + timedelta(days=1, hours=3)).strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': 'BTC/USDT',
                'timeframe': '15m',
                'signal': 'BUY',
                'action': 'close_short',
                'amount': 0.01,
                'price': 45500.0,  # 盈利
                'stop_loss': None,
                'take_profit': None,
                'confidence': 'MEDIUM',
                'reason': '达到止盈目标'
            },
            
            # 第三笔交易 - 亏损
            {
                'timestamp': (base_time + timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': 'BTC/USDT',
                'timeframe': '15m',
                'signal': 'BUY',
                'action': 'open_long',
                'amount': 0.01,
                'price': 46000.0,
                'stop_loss': 45000.0,
                'take_profit': 47000.0,
                'confidence': 'LOW',
                'reason': 'AI分析：弱看涨信号'
            },
            {
                'timestamp': (base_time + timedelta(days=2, hours=1)).strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': 'BTC/USDT',
                'timeframe': '15m',
                'signal': 'SELL',
                'action': 'close_long',
                'amount': 0.01,
                'price': 45200.0,  # 亏损
                'stop_loss': None,
                'take_profit': None,
                'confidence': 'LOW',
                'reason': '触发止损'
            }
        ]
        
        # 插入交易记录
        for i, trade in enumerate(test_trades, 1):
            record_trade(**trade)
            print(f"   {i}. {trade['action']} @ ${trade['price']}")
        
        print(f"✅ 成功创建 {len(test_trades)} 条测试交易记录")
        
        # 计算胜率
        print("\n📊 计算胜率...")
        stats = compute_win_rate_from_db()
        
        print(f"   胜率: {stats.get('win_rate', 0)}%")
        print(f"   总交易次数: {stats.get('total_trades', 0)}")
        print(f"   总盈亏: ${stats.get('total_profit', 0):.2f}")
        
        return stats
        
    except Exception as e:
        print(f"❌ 创建测试交易失败: {e}")
        import traceback
        traceback.print_exc()
        return None

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

def main():
    print("="*60)
    print("🧪 创建测试交易记录")
    print("="*60)
    
    try:
        # 加载环境变量
        from dotenv import load_dotenv
        load_dotenv()
        
        # 1. 清空现有记录
        if clear_existing_trades():
            # 2. 创建测试交易
            stats = create_test_trades()
            
            if stats:
                print("\n" + "="*60)
                print("✅ 测试数据创建完成！")
                print("💡 现在可以测试web界面的胜率显示")
                print("   预期胜率: 66.7% (2胜1负)")
                print(f"   实际胜率: {stats.get('win_rate', 0)}%")
                print("="*60)
            else:
                print("\n❌ 测试数据创建失败")
        
    except Exception as e:
        print(f"❌ 脚本执行失败: {e}")

if __name__ == "__main__":
    main()