#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速数据库检查脚本
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from paper_trading import _get_db_conn, compute_win_rate_from_db
        
        print("🔍 快速数据库检查")
        print("="*40)
        
        # 1. 检查连接
        conn = _get_db_conn()
        cursor = conn.cursor()
        
        # 2. 检查记录数量
        cursor.execute("SELECT COUNT(*) FROM trades")
        count = cursor.fetchone()[0]
        print(f"交易记录总数: {count}")
        
        if count > 0:
            # 3. 查看最近5条记录
            cursor.execute("SELECT timestamp, action, price FROM trades ORDER BY id DESC LIMIT 5")
            records = cursor.fetchall()
            
            print("\n最近5条记录:")
            for record in records:
                timestamp, action, price = record
                print(f"  {timestamp} - {action} @ ${price:.2f}")
            
            # 4. 计算胜率
            print("\n胜率计算:")
            stats = compute_win_rate_from_db()
            print(f"  胜率: {stats.get('win_rate', 0)}%")
            print(f"  总交易: {stats.get('total_trades', 0)}")
            print(f"  总盈亏: ${stats.get('total_profit', 0):.2f}")
        else:
            print("⚠️ 数据库中没有交易记录")
        
        cursor.close()
        conn.close()
        
        # 5. 检查web_data
        try:
            import deepseekok2
            performance = deepseekok2.web_data.get('performance', {})
            print(f"\nweb_data胜率: {performance.get('win_rate', 'N/A')}")
        except:
            print("\nweb_data检查失败")
        
        print("="*40)
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    main()