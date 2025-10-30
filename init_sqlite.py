#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
import json
from datetime import datetime

def create_data_directory():
    """创建数据目录"""
    data_dir = './data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print("✅ 创建数据目录: {}".format(data_dir))
    else:
        print("📁 数据目录已存在: {}".format(data_dir))

def get_btc_price():
    """获取BTC价格（简化版本）"""
    try:
        import urllib.request
        response = urllib.request.urlopen("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5)
        data = json.loads(response.read().decode())
        return float(data['price'])
    except:
        return 108254.04  # 默认价格

def init_sqlite_database():
    """初始化SQLite数据库"""
    db_path = './data/paper_trades.db'
    
    try:
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
        print("✅ SQLite数据库初始化成功: {}".format(db_path))
        
        # 添加示例数据
        btc_price = get_btc_price()
        print("💰 当前BTC价格: ${:,.2f}".format(btc_price))
        
        # 清除旧数据
        cursor.execute("DELETE FROM trades")
        cursor.execute("DELETE FROM positions")
        
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
        
        # 验证数据
        cursor.execute("SELECT COUNT(*) FROM trades")
        trade_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM positions")
        position_count = cursor.fetchone()[0]
        
        print("📊 交易记录数量: {}".format(trade_count))
        print("📊 持仓记录数量: {}".format(position_count))
        
        conn.close()
        return True
        
    except Exception as e:
        print("❌ SQLite数据库初始化失败: {}".format(str(e)))
        return False

def main():
    print("🔄 初始化SQLite数据库...")
    print("=" * 40)
    
    # 创建数据目录
    create_data_directory()
    
    # 初始化数据库
    if init_sqlite_database():
        print("\n🎉 SQLite数据库初始化完成！")
        print("现在可以启动web服务器:")
        print("python3 web_server.py")
    else:
        print("\n❌ SQLite数据库初始化失败")

if __name__ == "__main__":
    main()