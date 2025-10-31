#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VPS数据库直接检查脚本 - 无需MySQL客户端
适用于Python 3.6环境
"""

import os
import sys

def check_database_with_python():
    """使用Python直接检查数据库"""
    try:
        # 尝试导入数据库模块
        try:
            import mysql.connector
            use_mysql_connector = True
            print("✅ 使用mysql.connector")
        except ImportError:
            try:
                import pymysql
                use_mysql_connector = False
                print("✅ 使用pymysql")
            except ImportError:
                print("❌ 没有可用的MySQL Python模块")
                return False
        
        # 从环境变量获取数据库配置
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'trading_bot')
        }
        
        print("🔍 数据库配置:")
        print(f"   主机: {db_config['host']}")
        print(f"   用户: {db_config['user']}")
        print(f"   数据库: {db_config['database']}")
        
        # 连接数据库
        if use_mysql_connector:
            conn = mysql.connector.connect(**db_config)
        else:
            conn = pymysql.connect(**db_config)
        
        cursor = conn.cursor()
        print("✅ 数据库连接成功")
        
        # 1. 检查表是否存在
        print("\n📋 检查数据表:")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        if not tables:
            print("   ⚠️ 数据库中没有表")
            return False
        
        for table in tables:
            print(f"   - {table[0]}")
        
        # 2. 检查trades表结构
        if ('trades',) in tables:
            print("\n🔍 trades表结构:")
            cursor.execute("DESCRIBE trades")
            columns = cursor.fetchall()
            
            for col in columns:
                print(f"   {col[0]} - {col[1]}")
        
        # 3. 检查记录数量
        print("\n📊 数据统计:")
        cursor.execute("SELECT COUNT(*) FROM trades")
        total_count = cursor.fetchone()[0]
        print(f"   总记录数: {total_count}")
        
        if total_count == 0:
            print("   ⚠️ trades表中没有数据")
            return True
        
        # 4. 按action分组统计
        cursor.execute("SELECT action, COUNT(*) FROM trades GROUP BY action")
        action_stats = cursor.fetchall()
        
        print("   按操作类型统计:")
        for action, count in action_stats:
            print(f"     {action}: {count}次")
        
        # 5. 查看最近的记录
        print("\n📝 最近10条记录:")
        cursor.execute("SELECT id, timestamp, action, price, amount FROM trades ORDER BY id DESC LIMIT 10")
        recent_records = cursor.fetchall()
        
        for record in recent_records:
            record_id, timestamp, action, price, amount = record
            print(f"   {record_id}: {timestamp} - {action} @ ${float(price):.2f} (数量: {float(amount)})")
        
        # 6. 检查开仓/平仓配对
        print("\n🔍 开仓/平仓配对分析:")
        
        # 统计各种操作
        cursor.execute("SELECT action, COUNT(*) FROM trades WHERE action LIKE 'open_%' GROUP BY action")
        open_actions = cursor.fetchall()
        
        cursor.execute("SELECT action, COUNT(*) FROM trades WHERE action LIKE 'close_%' GROUP BY action")
        close_actions = cursor.fetchall()
        
        print("   开仓操作:")
        total_opens = 0
        for action, count in open_actions:
            print(f"     {action}: {count}次")
            total_opens += count
        
        print("   平仓操作:")
        total_closes = 0
        for action, count in close_actions:
            print(f"     {action}: {count}次")
            total_closes += count
        
        print(f"   开仓总数: {total_opens}, 平仓总数: {total_closes}")
        
        if total_opens != total_closes:
            print("   ⚠️ 开仓和平仓数量不匹配！这可能导致胜率计算错误")
            
            # 检查是否有未平仓的交易
            unmatched = total_opens - total_closes
            if unmatched > 0:
                print(f"   📈 可能有 {unmatched} 笔未平仓的交易")
            else:
                print(f"   ❓ 平仓比开仓多 {abs(unmatched)} 笔，数据可能有问题")
        else:
            print("   ✅ 开仓和平仓数量匹配")
        
        # 7. 手动计算胜率
        if total_opens > 0 and total_closes > 0:
            print("\n🧮 手动胜率计算:")
            
            # 获取所有完整的交易对
            cursor.execute("""
                SELECT 
                    o.price as open_price, 
                    c.price as close_price,
                    o.action as open_action,
                    o.amount
                FROM trades o
                JOIN trades c ON o.id < c.id
                WHERE o.action LIKE 'open_%' AND c.action LIKE 'close_%'
                ORDER BY o.id
            """)
            
            trade_pairs = cursor.fetchall()
            
            if trade_pairs:
                wins = 0
                total_profit = 0.0
                
                for open_price, close_price, open_action, amount in trade_pairs:
                    open_price = float(open_price)
                    close_price = float(close_price)
                    amount = float(amount)
                    
                    if 'long' in open_action:
                        # 做多：平仓价格 > 开仓价格 = 盈利
                        profit = (close_price - open_price) * amount
                    else:
                        # 做空：开仓价格 > 平仓价格 = 盈利
                        profit = (open_price - close_price) * amount
                    
                    total_profit += profit
                    if profit > 0:
                        wins += 1
                    
                    print(f"     {open_action} @ ${open_price:.2f} -> ${close_price:.2f} = ${profit:.2f}")
                
                win_rate = (wins / len(trade_pairs)) * 100 if trade_pairs else 0
                print(f"\n   📊 计算结果:")
                print(f"     总交易对: {len(trade_pairs)}")
                print(f"     盈利交易: {wins}")
                print(f"     胜率: {win_rate:.1f}%")
                print(f"     总盈亏: ${total_profit:.2f}")
            else:
                print("   ❌ 无法找到匹配的交易对")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_env_file():
    """检查环境变量配置"""
    print("🔍 检查环境变量配置:")
    
    env_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME', 'DB_TYPE']
    
    for var in env_vars:
        value = os.getenv(var, '未设置')
        if var == 'DB_PASSWORD':
            value = '***' if value != '未设置' else '未设置'
        print(f"   {var}: {value}")

def main():
    print("="*60)
    print("🔍 VPS数据库直接检查")
    print("="*60)
    
    # 1. 检查环境变量
    check_env_file()
    
    print("\n" + "="*60)
    
    # 2. 检查数据库
    success = check_database_with_python()
    
    print("\n" + "="*60)
    if success:
        print("✅ 数据库检查完成")
    else:
        print("❌ 数据库检查失败")
    print("="*60)

if __name__ == "__main__":
    main()