import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'paper_trades.db')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        '''CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol TEXT,
            timeframe TEXT,
            signal TEXT,
            action TEXT,
            amount REAL,
            price REAL,
            stop_loss REAL,
            take_profit REAL,
            confidence TEXT,
            reason TEXT
        )'''
    )
    conn.commit()
    conn.close()


def record_trade(signal_data, price_data, action, amount):
    # Ensure DB exists
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        'CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, symbol TEXT, timeframe TEXT, signal TEXT, action TEXT, amount REAL, price REAL, stop_loss REAL, take_profit REAL, confidence TEXT, reason TEXT)'
    )

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    symbol = price_data.get('symbol', 'BTC/USDT')
    timeframe = price_data.get('timeframe', '15m')
    signal = signal_data.get('signal')
    confidence = signal_data.get('confidence')
    reason = signal_data.get('reason')
    price = price_data.get('price', 0.0)
    stop_loss = signal_data.get('stop_loss', None)
    take_profit = signal_data.get('take_profit', None)

    c.execute(
        'INSERT INTO trades (timestamp, symbol, timeframe, signal, action, amount, price, stop_loss, take_profit, confidence, reason) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
        (timestamp, symbol, timeframe, signal, action, amount, price, stop_loss, take_profit, confidence, reason)
    )

    conn.commit()
    conn.close()


def get_last_trade():
    """读取最近一条交易记录，若无则返回None"""
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(
            'SELECT timestamp, symbol, timeframe, signal, action, amount, price, stop_loss, take_profit, confidence, reason '
            'FROM trades ORDER BY id DESC LIMIT 1'
        )
        row = c.fetchone()
        if not row:
            return None
        keys = ['timestamp', 'symbol', 'timeframe', 'signal', 'action', 'amount', 'price', 'stop_loss', 'take_profit', 'confidence', 'reason']
        return dict(zip(keys, row))
    finally:
        conn.close()


def get_last_open_trade():
    """读取最近一次开仓记录（open_long/open_short），若无则返回None"""
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(
            """
            SELECT timestamp, symbol, timeframe, signal, action, amount, price, stop_loss, take_profit, confidence, reason
            FROM trades
            WHERE action IN ('open_long','open_short')
            ORDER BY id DESC LIMIT 1
            """
        )
        row = c.fetchone()
        if not row:
            return None
        keys = ['timestamp', 'symbol', 'timeframe', 'signal', 'action', 'amount', 'price', 'stop_loss', 'take_profit', 'confidence', 'reason']
        return dict(zip(keys, row))
    finally:
        conn.close()