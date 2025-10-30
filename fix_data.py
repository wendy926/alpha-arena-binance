#!/usr/bin/env python3
"""
修复数据脚本：清理旧数据并添加新的测试交易记录
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from paper_trading import init_db, record_trade, get_all_trades, compute_win_rate_from_db
from deepseekok2 import get_real_btc_price
import sqlite3
from datetime import datetime, timedelta

def clear_old_data():
    """清理旧的交易数据"""
    try:
        conn = sqlite3.connect('data/paper_trades.db')
        cursor = conn.cursor()
        
        # 删除所有旧记录
        cursor.execute("DELETE FROM trades")
        conn.commit()
        conn.close()
        print("✅ 已清理所有旧交易记录")
        return True
    except Exception as e:
        print(f"❌ 清理数据失败: {e}")
        return False

def add_test_trades():
    """添加一些测试交易记录"""
    try:
        # 获取当前BTC价格
        current_price = get_real_btc_price()
        print(f"💰 当前BTC价格: ${current_price:,.2f}")
        
        # 模拟一些交易记录
        base_time = datetime.now() - timedelta(days=7)
        
        trades = [
            # 第一笔交易 - 盈利
            {
                'action': 'open_long',
                'price': current_price - 2000,  # 较低价格开多
                'amount': 0.01,
                'timestamp': base_time + timedelta(days=1)
            },
            {
                'action': 'close_long', 
                'price': current_price - 1500,  # 较高价格平多，盈利
                'amount': 0.01,
                'timestamp': base_time + timedelta(days=1, hours=2)
            },
            
            # 第二笔交易 - 亏损
            {
                'action': 'open_short',
                'price': current_price - 1000,  # 较高价格开空
                'amount': 0.01,
                'timestamp': base_time + timedelta(days=2)
            },
            {
                'action': 'close_short',
                'price': current_price - 800,   # 更高价格平空，亏损
                'amount': 0.01,
                'timestamp': base_time + timedelta(days=2, hours=3)
            },
            
            # 第三笔交易 - 盈利
            {
                'action': 'open_long',
                'price': current_price - 500,   # 较低价格开多
                'amount': 0.01,
                'timestamp': base_time + timedelta(days=3)
            },
            {
                'action': 'close_long',
                'price': current_price - 200,   # 较高价格平多，盈利
                'amount': 0.01,
                'timestamp': base_time + timedelta(days=3, hours=4)
            },
            
            # 当前持仓 - 开多
            {
                'action': 'open_long',
                'price': current_price - 100,   # 接近当前价格开多
                'amount': 0.01,
                'timestamp': base_time + timedelta(days=4)
            }
        ]
        
        for trade in trades:
            record_trade(
                action=trade['action'],
                price=trade['price'],
                amount=trade['amount'],
                timestamp=trade['timestamp'].isoformat()
            )
            print(f"📝 记录交易: {trade['action']} @ ${trade['price']:,.2f}")
        
        print("✅ 已添加测试交易记录")
        return True
        
    except Exception as e:
        print(f"❌ 添加测试数据失败: {e}")
        return False

def main():
    print("=== 修复交易数据 ===")
    
    # 初始化数据库
    init_db()
    
    # 清理旧数据
    if not clear_old_data():
        return
    
    # 添加新的测试数据
    if not add_test_trades():
        return
    
    # 验证结果
    trades = get_all_trades()
    print(f"\n📊 数据库中现有 {len(trades)} 条交易记录")
    
    # 计算胜率
    stats = compute_win_rate_from_db()
    print(f"\n📈 胜率统计:")
    print(f"  - 胜率: {stats.get('win_rate', 0):.1f}%")
    print(f"  - 总交易次数: {stats.get('total_trades', 0)}")
    print(f"  - 总盈亏: ${stats.get('total_profit', 0):.2f}")
    
    print("\n✅ 数据修复完成！请重启服务并刷新页面查看效果。")

if __name__ == "__main__":
    main()