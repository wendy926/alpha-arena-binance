#!/usr/bin/env python3
"""
详细调试和修复胜率计算问题
"""
import os
import sys
import traceback

# 设置环境变量
os.environ['DB_TYPE'] = 'mysql'
os.environ['MYSQL_HOST'] = 'localhost'
os.environ['MYSQL_PORT'] = '3306'
os.environ['MYSQL_USER'] = 'trader'
os.environ['MYSQL_PASSWORD'] = 'trader123'
os.environ['MYSQL_DB'] = 'trading_bot'

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

def test_database_connection():
    """测试数据库连接"""
    print("🔗 测试数据库连接...")
    try:
        import pymysql
        conn = pymysql.connect(
            host='localhost',
            port=3306,
            user='trader',
            password='trader123',
            database='trading_bot',
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM trades")
        count = cursor.fetchone()[0]
        print(f"   ✅ 数据库连接成功，trades表有 {count} 条记录")
        
        # 查看具体记录
        cursor.execute("SELECT id, timestamp, action, amount, price, reason FROM trades ORDER BY timestamp ASC")
        rows = cursor.fetchall()
        print(f"   📊 具体记录:")
        for row in rows:
            print(f"     ID:{row[0]} {row[1]} {row[2]} amount:{row[3]} price:{row[4]} reason:{row[5]}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"   ❌ 数据库连接失败: {e}")
        return False

def test_paper_trading_import():
    """测试paper_trading模块导入"""
    print("\n📦 测试paper_trading模块导入...")
    try:
        from paper_trading import compute_win_rate_from_db, get_all_trades, _get_db_conn
        print("   ✅ 模块导入成功")
        return True
    except Exception as e:
        print(f"   ❌ 模块导入失败: {e}")
        traceback.print_exc()
        return False

def debug_get_all_trades():
    """调试get_all_trades函数"""
    print("\n📋 调试get_all_trades函数...")
    try:
        from paper_trading import get_all_trades
        trades = get_all_trades()
        print(f"   ✅ 获取到 {len(trades)} 条交易记录")
        
        for i, trade in enumerate(trades):
            print(f"   记录 {i+1}: {trade}")
            
        return trades
    except Exception as e:
        print(f"   ❌ 获取交易记录失败: {e}")
        traceback.print_exc()
        return []

def debug_compute_win_rate():
    """调试compute_win_rate_from_db函数"""
    print("\n🧮 调试compute_win_rate_from_db函数...")
    try:
        from paper_trading import compute_win_rate_from_db
        result = compute_win_rate_from_db()
        print(f"   ✅ 胜率计算结果: {result}")
        return result
    except Exception as e:
        print(f"   ❌ 胜率计算失败: {e}")
        traceback.print_exc()
        return None

def manual_winrate_calculation(trades):
    """手动计算胜率"""
    print("\n🔧 手动计算胜率...")
    
    current_side = None
    entry_price = None
    size = 0.0
    wins = 0
    total = 0
    total_profit = 0.0
    
    print(f"   处理 {len(trades)} 条记录...")
    
    for i, t in enumerate(trades):
        action = (t.get('action') or '').lower()
        raw_price = t.get('price')
        raw_amount = t.get('amount')
        
        print(f"\n   记录 {i+1}:")
        print(f"     action: '{action}'")
        print(f"     raw_price: {raw_price} (type: {type(raw_price)})")
        print(f"     raw_amount: {raw_amount} (type: {type(raw_amount)})")
        
        # 数据验证
        if raw_price is None or raw_price == '' or raw_amount is None or raw_amount == '':
            print(f"     ⚠️ 跳过无效记录")
            continue
            
        try:
            price = float(raw_price)
            amount = float(raw_amount)
            
            if price <= 0 or amount <= 0:
                print(f"     ⚠️ 跳过零值记录")
                continue
                
        except (ValueError, TypeError) as e:
            print(f"     ⚠️ 数据转换失败: {e}")
            continue
        
        print(f"     ✅ 有效数据: price={price}, amount={amount}")
        
        # 处理开仓
        if action in ('open_long', 'open_short'):
            current_side = 'long' if action == 'open_long' else 'short'
            entry_price = price
            size = amount
            print(f"     📈 开仓: side={current_side}, entry_price={entry_price}, size={size}")
            
        # 处理平仓
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
                
            print(f"     📉 平仓: exit_price={price}, pnl={pnl:.6f}")
            print(f"     📊 当前统计: wins={wins}, total={total}, total_profit={total_profit:.6f}")
            
            # 重置仓位
            current_side = None
            entry_price = None
            size = 0.0
            
        else:
            print(f"     ⚠️ 无法处理: action='{action}', current_side={current_side}")
    
    # 最终结果
    win_rate = (wins / total * 100.0) if total else 0.0
    print(f"\n   📈 手动计算结果:")
    print(f"     胜利次数: {wins}")
    print(f"     总交易次数: {total}")
    print(f"     胜率: {win_rate:.1f}%")
    print(f"     总盈亏: ${total_profit:.6f}")
    
    return {'win_rate': win_rate, 'total_trades': total, 'total_profit': total_profit}

def main():
    """主函数"""
    print("🔍 开始详细调试胜率计算问题")
    print("=" * 50)
    
    # 1. 测试数据库连接
    if not test_database_connection():
        return
    
    # 2. 测试模块导入
    if not test_paper_trading_import():
        return
    
    # 3. 调试get_all_trades
    trades = debug_get_all_trades()
    if not trades:
        print("❌ 没有交易记录，无法继续")
        return
    
    # 4. 调试官方胜率计算
    official_result = debug_compute_win_rate()
    
    # 5. 手动计算胜率
    manual_result = manual_winrate_calculation(trades)
    
    # 6. 对比结果
    print(f"\n🔄 结果对比:")
    print(f"   官方结果: {official_result}")
    print(f"   手动结果: {manual_result}")
    
    if official_result and manual_result:
        if official_result['win_rate'] != manual_result['win_rate']:
            print("   ⚠️ 结果不一致，可能存在bug")
        else:
            print("   ✅ 结果一致")

if __name__ == "__main__":
    main()