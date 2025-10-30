#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断胜率显示问题
检查数据库连接、交易记录和胜率计算
"""

import os
import sys
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_env():
    """加载环境变量"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ 环境变量加载成功")
    except Exception as e:
        print(f"⚠️ 环境变量加载失败: {e}")

def check_database_config():
    """检查数据库配置"""
    print("\n🔍 数据库配置检查:")
    
    db_type = os.getenv('DB_TYPE', 'sqlite')
    print(f"   数据库类型: {db_type}")
    
    if db_type.lower() == 'mysql':
        print(f"   MySQL主机: {os.getenv('MYSQL_HOST', 'localhost')}")
        print(f"   MySQL端口: {os.getenv('MYSQL_PORT', '3306')}")
        print(f"   MySQL用户: {os.getenv('MYSQL_USER', 'alpha')}")
        print(f"   MySQL数据库: {os.getenv('MYSQL_DB', 'alpha_arena')}")
        print(f"   MySQL密码: {'已设置' if os.getenv('MYSQL_PASSWORD') else '未设置'}")
    else:
        db_path = os.path.join(os.path.dirname(__file__), 'paper_trades.db')
        print(f"   SQLite路径: {db_path}")
        print(f"   SQLite文件存在: {os.path.exists(db_path)}")

def test_database_connection():
    """测试数据库连接"""
    print("\n🔍 数据库连接测试:")
    
    try:
        from paper_trading import _get_db_conn, list_trades, get_all_trades, compute_win_rate_from_db
        
        # 测试连接
        conn = _get_db_conn()
        print("✅ 数据库连接成功")
        
        # 检查表是否存在
        c = conn.cursor()
        db_type = os.getenv('DB_TYPE', 'sqlite').lower()
        
        if db_type == 'mysql':
            c.execute("SHOW TABLES LIKE 'trades'")
            table_exists = c.fetchone() is not None
        else:
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades'")
            table_exists = c.fetchone() is not None
            
        print(f"   trades表存在: {table_exists}")
        
        if table_exists:
            # 检查记录数量
            c.execute("SELECT COUNT(*) FROM trades")
            count = c.fetchone()[0]
            print(f"   交易记录总数: {count}")
            
            # 获取最近几条记录
            if count > 0:
                print("\n📋 最近5条交易记录:")
                recent_trades = list_trades(limit=5)
                for i, trade in enumerate(recent_trades, 1):
                    print(f"   {i}. {trade.get('timestamp', 'N/A')} - {trade.get('action', 'N/A')} @ ${trade.get('price', 0):.2f}")
                
                # 测试胜率计算
                print("\n📊 胜率计算测试:")
                stats = compute_win_rate_from_db()
                print(f"   胜率: {stats.get('win_rate', 'N/A')}")
                print(f"   总交易次数: {stats.get('total_trades', 'N/A')}")
                print(f"   总盈亏: ${stats.get('total_profit', 0):.2f}")
                
                return stats
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_web_data():
    """测试web_data中的performance数据"""
    print("\n🔍 Web数据检查:")
    
    try:
        import deepseekok2
        
        performance = deepseekok2.web_data.get('performance', {})
        print(f"   web_data中的胜率: {performance.get('win_rate', 'N/A')}")
        print(f"   web_data中的总交易: {performance.get('total_trades', 'N/A')}")
        print(f"   web_data中的总盈亏: {performance.get('total_profit', 'N/A')}")
        
        return performance
        
    except Exception as e:
        print(f"❌ Web数据检查失败: {e}")
        return None

def diagnose_api_issue():
    """诊断API数据同步问题"""
    print("\n🔍 API数据同步诊断:")
    
    # 1. 检查数据库胜率
    db_stats = test_database_connection()
    
    # 2. 检查web_data胜率
    web_performance = test_web_data()
    
    # 3. 对比分析
    if db_stats and web_performance:
        db_win_rate = db_stats.get('win_rate', 0)
        web_win_rate = web_performance.get('win_rate', 0)
        
        print(f"\n📊 数据对比:")
        print(f"   数据库胜率: {db_win_rate}")
        print(f"   Web数据胜率: {web_win_rate}")
        
        if db_win_rate != web_win_rate:
            print("❌ 数据不同步！数据库和Web数据中的胜率不一致")
            return False
        else:
            print("✅ 数据同步正常")
            return True
    
    return False

if __name__ == "__main__":
    print("="*60)
    print("🔍 胜率显示问题诊断")
    print("="*60)
    
    # 1. 加载环境变量
    load_env()
    
    # 2. 检查数据库配置
    check_database_config()
    
    # 3. 测试数据库连接和数据
    test_database_connection()
    
    # 4. 诊断API数据同步
    is_synced = diagnose_api_issue()
    
    print("\n" + "="*60)
    if is_synced:
        print("✅ 诊断完成：数据同步正常")
        print("💡 建议：检查前端JavaScript是否正确处理API返回的数据")
    else:
        print("❌ 诊断完成：发现数据同步问题")
        print("💡 建议：检查API端点中的胜率计算逻辑")
    print("="*60)