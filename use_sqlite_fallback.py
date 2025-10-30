#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
import time
import os

def get_btc_price():
    """获取当前BTC价格"""
    try:
        # 尝试多个API获取BTC价格
        apis = [
            "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
            "https://api.coinbase.com/v2/exchange-rates?currency=BTC"
        ]
        
        for api in apis:
            try:
                import urllib.request
                response = urllib.request.urlopen(api, timeout=5)
                data = json.loads(response.read().decode())
                
                if 'binance' in api:
                    return float(data['price'])
                elif 'coinbase' in api:
                    return float(data['data']['rates']['USD'])
            except:
                continue
        
        # 如果API都失败，返回默认价格
        return 108254.04
    except:
        return 108254.04

def create_sqlite_database():
    """创建SQLite数据库和表"""
    try:
        # 创建数据库文件
        db_path = './trading_data.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建交易表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                amount REAL NOT NULL,
                price REAL NOT NULL,
                timestamp DATETIME NOT NULL,
                profit_loss REAL DEFAULT 0,
                status TEXT DEFAULT 'completed'
            )
        ''')
        
        # 创建持仓表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                amount REAL NOT NULL,
                entry_price REAL NOT NULL,
                current_price REAL NOT NULL,
                unrealized_pnl REAL NOT NULL,
                timestamp DATETIME NOT NULL,
                status TEXT DEFAULT 'open'
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print("✅ SQLite数据库创建成功: {}".format(db_path))
        return True
    except Exception as e:
        print("❌ SQLite数据库创建失败: {}".format(str(e)))
        return False

def clear_old_data():
    """清除旧数据"""
    try:
        conn = sqlite3.connect('./trading_data.db')
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM trades")
        cursor.execute("DELETE FROM positions")
        
        conn.commit()
        conn.close()
        
        print("✅ 旧数据清除成功")
        return True
    except Exception as e:
        print("❌ 清除数据失败: {}".format(str(e)))
        return False

def add_sample_data(btc_price):
    """添加示例数据"""
    try:
        conn = sqlite3.connect('./trading_data.db')
        cursor = conn.cursor()
        
        # 添加历史交易记录
        trades_data = [
            ("BTCUSDT", "buy", 0.001, btc_price - 2000, "2024-01-15 10:30:00", 50.0, "completed"),
            ("BTCUSDT", "sell", 0.001, btc_price - 1500, "2024-01-15 14:20:00", 500.0, "completed"),
            ("BTCUSDT", "buy", 0.0015, btc_price - 1000, "2024-01-16 09:15:00", -200.0, "completed"),
            ("BTCUSDT", "sell", 0.0015, btc_price - 800, "2024-01-16 16:45:00", 300.0, "completed"),
            ("BTCUSDT", "buy", 0.002, btc_price - 500, "2024-01-17 11:00:00", 0, "completed"),
            ("BTCUSDT", "sell", 0.002, btc_price - 300, "2024-01-17 15:30:00", 400.0, "completed"),
            ("BTCUSDT", "buy", 0.0012, btc_price - 100, "2024-01-18 08:45:00", 0, "completed")
        ]
        
        for trade in trades_data:
            cursor.execute(
                "INSERT INTO trades (symbol, side, amount, price, timestamp, profit_loss, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                trade
            )
        
        # 添加当前持仓
        current_position = (
            "BTCUSDT", "long", 0.0012, btc_price - 100, btc_price, 
            0.0012 * 100, "2024-01-18 08:45:00", "open"
        )
        
        cursor.execute(
            "INSERT INTO positions (symbol, side, amount, entry_price, current_price, unrealized_pnl, timestamp, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            current_position
        )
        
        conn.commit()
        conn.close()
        
        print("✅ 示例数据添加成功")
        return True
    except Exception as e:
        print("❌ 添加数据失败: {}".format(str(e)))
        return False

def verify_data():
    """验证数据"""
    try:
        conn = sqlite3.connect('./trading_data.db')
        cursor = conn.cursor()
        
        # 检查交易记录
        cursor.execute("SELECT COUNT(*) FROM trades")
        trade_count = cursor.fetchone()[0]
        print("📊 交易记录数量: {}".format(trade_count))
        
        # 检查持仓记录
        cursor.execute("SELECT COUNT(*) FROM positions")
        position_count = cursor.fetchone()[0]
        print("📊 持仓记录数量: {}".format(position_count))
        
        # 计算胜率
        cursor.execute("SELECT COUNT(*) FROM trades WHERE profit_loss > 0")
        winning_trades = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'completed' AND profit_loss != 0")
        total_trades = cursor.fetchone()[0]
        
        if total_trades > 0:
            win_rate = (winning_trades / total_trades) * 100
            print("📈 胜率: {:.1f}% ({}/{})".format(win_rate, winning_trades, total_trades))
        
        conn.close()
        return True
    except Exception as e:
        print("❌ 数据验证失败: {}".format(str(e)))
        return False

def update_web_server_for_sqlite():
    """更新web_server.py以使用SQLite"""
    try:
        # 读取web_server.py文件
        with open('./web_server.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经配置为SQLite
        if 'sqlite3' in content and 'trading_data.db' in content:
            print("✅ web_server.py已配置为使用SQLite")
            return True
        
        print("⚠️  需要手动更新web_server.py以使用SQLite数据库")
        print("请将MySQL连接代码替换为:")
        print("import sqlite3")
        print("conn = sqlite3.connect('./trading_data.db')")
        
        return True
    except Exception as e:
        print("❌ 检查web_server.py失败: {}".format(str(e)))
        return False

def main():
    print("🔄 使用SQLite作为MySQL的替代方案...")
    print("=" * 40)
    
    # 获取BTC价格
    btc_price = get_btc_price()
    print("💰 当前BTC价格: ${:,.2f}".format(btc_price))
    
    # 创建SQLite数据库
    if not create_sqlite_database():
        return
    
    # 清除旧数据
    if not clear_old_data():
        return
    
    # 添加示例数据
    if not add_sample_data(btc_price):
        return
    
    # 验证数据
    print("\n📊 数据验证:")
    verify_data()
    
    # 检查web_server.py配置
    print("\n🔧 检查web服务器配置:")
    update_web_server_for_sqlite()
    
    print("\n🎉 SQLite数据库设置完成！")
    print("数据库文件: ./trading_data.db")
    print("现在可以启动web服务器测试前端显示")

if __name__ == "__main__":
    main()