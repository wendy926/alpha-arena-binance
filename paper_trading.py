import os
import sqlite3
from datetime import datetime

# MySQL 可选支持
try:
    import pymysql
    _MYSQL_AVAILABLE = True
except Exception:
    pymysql = None
    _MYSQL_AVAILABLE = False

DB_TYPE = os.getenv('DB_TYPE', 'sqlite').lower()  # 'sqlite' 或 'mysql'
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
MYSQL_USER = os.getenv('MYSQL_USER', 'alpha')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
MYSQL_DB = os.getenv('MYSQL_DB', 'alpha_arena')

DB_PATH = os.path.join(os.path.dirname(__file__), 'paper_trades.db')


def _get_db_conn():
    """根据 DB_TYPE 返回数据库连接。MySQL需预先创建数据库。"""
    if DB_TYPE == 'mysql':
        if not _MYSQL_AVAILABLE:
            raise RuntimeError('pymysql 不可用，请安装并设置 DB_TYPE=sqlite 或安装pymysql')
        return pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            charset='utf8mb4',
            autocommit=False
        )
    # 默认sqlite
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = _get_db_conn()
    c = conn.cursor()
    if DB_TYPE == 'mysql':
        c.execute(
            '''CREATE TABLE IF NOT EXISTS trades (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME,
                symbol VARCHAR(32),
                timeframe VARCHAR(16),
                `signal` VARCHAR(8),
                action VARCHAR(16),
                amount DOUBLE,
                price DOUBLE,
                stop_loss DOUBLE,
                take_profit DOUBLE,
                confidence VARCHAR(8),
                reason VARCHAR(255)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4'''
        )
    else:
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
    """写入一条交易记录（开/平仓）到数据库。"""
    conn = _get_db_conn()
    c = conn.cursor()
    # 确保表存在
    init_db()

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    symbol = price_data.get('symbol', 'BTC/USDT')
    timeframe = price_data.get('timeframe', '15m')
    signal = signal_data.get('signal')
    confidence = signal_data.get('confidence')
    reason = signal_data.get('reason')
    price = float(price_data.get('price', 0.0) or 0.0)
    stop_loss = signal_data.get('stop_loss', None)
    take_profit = signal_data.get('take_profit', None)

    if DB_TYPE == 'mysql':
        sql = ('INSERT INTO trades (timestamp, symbol, timeframe, `signal`, action, amount, price, stop_loss, take_profit, confidence, reason) '
               'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)')
        params = (timestamp, symbol, timeframe, signal, action, float(amount or 0.0), price, stop_loss, take_profit, confidence, reason)
    else:
        sql = ('INSERT INTO trades (timestamp, symbol, timeframe, signal, action, amount, price, stop_loss, take_profit, confidence, reason) '
               'VALUES (?,?,?,?,?,?,?,?,?,?,?)')
        params = (timestamp, symbol, timeframe, signal, action, float(amount or 0.0), price, stop_loss, take_profit, confidence, reason)

    c.execute(sql, params)
    conn.commit()
    conn.close()


def get_last_trade():
    """读取最近一条交易记录，若无则返回None"""
    if DB_TYPE == 'sqlite' and not os.path.exists(DB_PATH):
        return None
    conn = _get_db_conn()
    c = conn.cursor()
    try:
        if DB_TYPE == 'mysql':
            c.execute('SELECT timestamp, symbol, timeframe, `signal`, action, amount, price, stop_loss, take_profit, confidence, reason FROM trades ORDER BY id DESC LIMIT 1')
        else:
            c.execute('SELECT timestamp, symbol, timeframe, signal, action, amount, price, stop_loss, take_profit, confidence, reason FROM trades ORDER BY id DESC LIMIT 1')
        row = c.fetchone()
        if not row:
            return None
        keys = ['timestamp', 'symbol', 'timeframe', 'signal', 'action', 'amount', 'price', 'stop_loss', 'take_profit', 'confidence', 'reason']
        # MySQL 默认返回元组；sqlite也是元组
        return dict(zip(keys, row))
    finally:
        conn.close()


def get_last_open_trade():
    """读取最近一次开仓记录（open_long/open_short），若无则返回None"""
    if DB_TYPE == 'sqlite' and not os.path.exists(DB_PATH):
        return None
    conn = _get_db_conn()
    c = conn.cursor()
    try:
        sql = ("""
            SELECT timestamp, symbol, timeframe, signal, action, amount, price, stop_loss, take_profit, confidence, reason
            FROM trades
            WHERE action IN ('open_long','open_short')
            ORDER BY id DESC LIMIT 1
        """)
        c.execute(sql)
        row = c.fetchone()
        if not row:
            return None
        keys = ['timestamp', 'symbol', 'timeframe', 'signal', 'action', 'amount', 'price', 'stop_loss', 'take_profit', 'confidence', 'reason']
        return dict(zip(keys, row))
    finally:
        conn.close()


def list_trades(limit=200):
    """返回最近的交易记录列表（按时间倒序）"""
    if DB_TYPE == 'sqlite' and not os.path.exists(DB_PATH):
        return []
    conn = _get_db_conn()
    c = conn.cursor()
    try:
        if DB_TYPE == 'mysql':
            c.execute('SELECT timestamp, symbol, timeframe, `signal`, action, amount, price, stop_loss, take_profit, confidence, reason FROM trades ORDER BY id DESC LIMIT %s', (int(limit or 200),))
        else:
            c.execute('SELECT timestamp, symbol, timeframe, signal, action, amount, price, stop_loss, take_profit, confidence, reason FROM trades ORDER BY id DESC LIMIT ?', (int(limit or 200),))
        rows = c.fetchall()
        keys = ['timestamp', 'symbol', 'timeframe', 'signal', 'action', 'amount', 'price', 'stop_loss', 'take_profit', 'confidence', 'reason']
        return [dict(zip(keys, r)) for r in rows]
    finally:
        conn.close()


def get_all_trades():
    """返回全部交易记录（按id升序），用于统计胜率"""
    if DB_TYPE == 'sqlite' and not os.path.exists(DB_PATH):
        return []
    conn = _get_db_conn()
    c = conn.cursor()
    try:
        if DB_TYPE == 'mysql':
            c.execute('SELECT timestamp, symbol, timeframe, `signal`, action, amount, price, stop_loss, take_profit, confidence, reason FROM trades ORDER BY id ASC')
        else:
            c.execute('SELECT timestamp, symbol, timeframe, signal, action, amount, price, stop_loss, take_profit, confidence, reason FROM trades ORDER BY id ASC')
        rows = c.fetchall()
        keys = ['timestamp', 'symbol', 'timeframe', 'signal', 'action', 'amount', 'price', 'stop_loss', 'take_profit', 'confidence', 'reason']
        return [dict(zip(keys, r)) for r in rows]
    finally:
        conn.close()


def compute_win_rate_from_db():
    """基于数据库记录计算胜率、总交易次数与总利润。
    规则：以 close_* 为一次交易的结束；与最近 open_* 配对计算盈亏。
    """
    trades = get_all_trades()
    if not trades:
        return {'win_rate': 0.0, 'total_trades': 0, 'total_profit': 0.0}

    current_side = None
    entry_price = None
    size = 0.0
    wins = 0
    total = 0
    total_profit = 0.0

    for t in trades:
        action = (t.get('action') or '').lower()
        
        # 修复：如果price或amount为None/空，跳过这条记录
        raw_price = t.get('price')
        raw_amount = t.get('amount')
        
        if raw_price is None or raw_price == '' or raw_amount is None or raw_amount == '':
            print(f"⚠️ 跳过无效记录: action={action}, price={raw_price}, amount={raw_amount}")
            continue
            
        try:
            price = float(raw_price)
            amount = float(raw_amount)
            
            # 检查是否为0值
            if price <= 0 or amount <= 0:
                print(f"⚠️ 跳过零值记录: action={action}, price={price}, amount={amount}")
                continue
                
        except (ValueError, TypeError):
            print(f"⚠️ 跳过无法转换的记录: action={action}, price={raw_price}, amount={raw_amount}")
            continue
        if action in ('open_long', 'open_short'):
            current_side = 'long' if action == 'open_long' else 'short'
            entry_price = price
            size = amount
        elif action in ('close_long', 'close_short') and current_side:
            pnl = 0.0
            if current_side == 'long':
                pnl = (price - entry_price) * size
            else:
                pnl = (entry_price - price) * size
            total_profit += pnl
            total += 1
            if pnl > 0:
                wins += 1
            # 重置仓位
            current_side = None
            entry_price = None
            size = 0.0

    win_rate = (wins / total * 100.0) if total else 0.0  # 转换为百分比
    print(f"📊 胜率计算结果: {wins}/{total} = {win_rate:.1f}%, 总盈亏: ${total_profit:.2f}")
    return {'win_rate': win_rate, 'total_trades': total, 'total_profit': total_profit}