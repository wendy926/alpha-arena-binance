#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从VPS同步交易数据到本地环境
"""

import os
import sys
import mysql.connector
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_env():
    """加载环境变量"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ 环境变量加载成功")
        return True
    except Exception as e:
        print(f"❌ 环境变量加载失败: {e}")
        return False

def connect_to_vps_mysql():
    """连接到VPS的MySQL数据库"""
    try:
        # VPS MySQL配置（从.env文件读取）
        vps_config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'user': os.getenv('MYSQL_USER', 'alpha'),
            'password': os.getenv('MYSQL_PASSWORD'),
            'database': os.getenv('MYSQL_DB', 'alpha_arena'),
            'charset': 'utf8mb4'
        }
        
        print(f"🔗 连接VPS MySQL: {vps_config['host']}:{vps_config['port']}")
        conn = mysql.connector.connect(**vps_config)
        print("✅ VPS MySQL连接成功")
        return conn
        
    except Exception as e:
        print(f"❌ VPS MySQL连接失败: {e}")
        return None

def get_vps_trades(vps_conn):
    """从VPS获取交易记录"""
    try:
        cursor = vps_conn.cursor(dictionary=True)
        
        # 获取所有交易记录
        cursor.execute("""
            SELECT * FROM trades 
            ORDER BY id ASC
        """)
        
        trades = cursor.fetchall()
        print(f"📊 VPS交易记录数量: {len(trades)}")
        
        if trades:
            print("📋 最近5条记录:")
            for i, trade in enumerate(trades[-5:], 1):
                print(f"   {i}. {trade.get('timestamp')} - {trade.get('action')} @ ${trade.get('price', 0):.2f}")
        
        cursor.close()
        return trades
        
    except Exception as e:
        print(f"❌ 获取VPS交易记录失败: {e}")
        return []

def sync_to_local_db(trades):
    """同步交易记录到本地数据库"""
    if not trades:
        print("⚠️ 没有交易记录需要同步")
        return False
    
    try:
        from paper_trading import _get_db_conn
        
        # 连接本地数据库
        local_conn = _get_db_conn()
        cursor = local_conn.cursor()
        
        # 清空现有记录（可选）
        print("🗑️ 清空本地交易记录...")
        cursor.execute("DELETE FROM trades")
        
        # 插入VPS的交易记录
        print(f"📥 同步 {len(trades)} 条交易记录...")
        
        for trade in trades:
            # 构建插入SQL
            columns = list(trade.keys())
            placeholders = ', '.join(['%s'] * len(columns))
            sql = f"INSERT INTO trades ({', '.join(columns)}) VALUES ({placeholders})"
            
            # 执行插入
            values = [trade[col] for col in columns]
            cursor.execute(sql, values)
        
        # 提交事务
        local_conn.commit()
        print("✅ 交易记录同步成功")
        
        # 验证同步结果
        cursor.execute("SELECT COUNT(*) FROM trades")
        count = cursor.fetchone()[0]
        print(f"📊 本地数据库现有记录: {count}")
        
        cursor.close()
        local_conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 同步到本地数据库失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_sync():
    """验证同步后的胜率计算"""
    try:
        from paper_trading import compute_win_rate_from_db
        
        print("\n🔍 验证同步后的胜率计算...")
        stats = compute_win_rate_from_db()
        
        print(f"📊 同步后胜率: {stats.get('win_rate', 0)}%")
        print(f"📊 总交易次数: {stats.get('total_trades', 0)}")
        print(f"📊 总盈亏: ${stats.get('total_profit', 0):.2f}")
        
        return stats
        
    except Exception as e:
        print(f"❌ 胜率验证失败: {e}")
        return None

def main():
    print("="*60)
    print("🔄 VPS交易数据同步脚本")
    print("="*60)
    
    # 1. 加载环境变量
    if not load_env():
        return
    
    # 2. 连接VPS MySQL
    vps_conn = connect_to_vps_mysql()
    if not vps_conn:
        print("❌ 无法连接VPS数据库，请检查配置")
        return
    
    try:
        # 3. 获取VPS交易记录
        trades = get_vps_trades(vps_conn)
        
        # 4. 同步到本地数据库
        if sync_to_local_db(trades):
            # 5. 验证同步结果
            verify_sync()
            
            print("\n" + "="*60)
            print("✅ 数据同步完成！")
            print("💡 现在可以重启web服务器查看更新后的胜率")
            print("   命令: python web_server.py")
            print("="*60)
        else:
            print("\n❌ 数据同步失败")
            
    finally:
        vps_conn.close()

if __name__ == "__main__":
    main()