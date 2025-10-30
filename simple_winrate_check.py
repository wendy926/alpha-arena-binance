#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的胜率检查脚本
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🔍 简化胜率检查")
    print("="*40)
    
    try:
        # 1. 加载环境变量
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ 环境变量加载成功")
        
        # 2. 检查数据库胜率
        from paper_trading import compute_win_rate_from_db
        stats = compute_win_rate_from_db()
        print(f"📊 数据库胜率: {stats.get('win_rate', 0)}%")
        print(f"📊 总交易次数: {stats.get('total_trades', 0)}")
        
        # 3. 检查web_data
        import deepseekok2
        performance = deepseekok2.web_data.get('performance', {})
        print(f"🌐 web_data胜率: {performance.get('win_rate', 'N/A')}")
        
        # 4. 简单结论
        db_rate = stats.get('win_rate', 0)
        web_rate = performance.get('win_rate', 0)
        
        if db_rate == web_rate:
            print("✅ 数据同步正常")
        else:
            print(f"❌ 数据不同步: DB={db_rate}, Web={web_rate}")
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()