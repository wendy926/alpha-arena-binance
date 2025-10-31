#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合诊断脚本 - 检查生产环境盈亏为0、胜率100%的问题
"""

import os
import sys
import requests
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_local_environment():
    """检查本地环境"""
    print("🔍 1. 检查本地环境...")
    
    try:
        # 检查环境变量
        from dotenv import load_dotenv
        load_dotenv()
        
        db_type = os.getenv('DB_TYPE', 'sqlite')
        print(f"   数据库类型: {db_type}")
        
        if db_type == 'mysql':
            print(f"   MySQL主机: {os.getenv('MYSQL_HOST', 'localhost')}")
            print(f"   MySQL端口: {os.getenv('MYSQL_PORT', '3306')}")
            print(f"   MySQL用户: {os.getenv('MYSQL_USER', 'alpha')}")
            print(f"   MySQL数据库: {os.getenv('MYSQL_DB', 'alpha_arena')}")
        
        # 检查paper_trading.py文件
        paper_trading_path = os.path.join(os.path.dirname(__file__), 'paper_trading.py')
        if os.path.exists(paper_trading_path):
            with open(paper_trading_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if '跳过无效记录' in content:
                    print("   ✅ paper_trading.py已包含修复代码")
                else:
                    print("   ❌ paper_trading.py未包含修复代码")
        
        return True
    except Exception as e:
        print(f"   ❌ 本地环境检查失败: {e}")
        return False

def check_local_database():
    """检查本地数据库"""
    print("\n🔍 2. 检查本地数据库...")
    
    try:
        from paper_trading import _get_db_conn, get_all_trades, compute_win_rate_from_db
        
        # 检查数据库连接
        conn = _get_db_conn()
        c = conn.cursor()
        
        # 检查记录数量
        if os.getenv('DB_TYPE', 'sqlite').lower() == 'mysql':
            c.execute("SELECT COUNT(*) FROM trades")
        else:
            c.execute("SELECT COUNT(*) FROM trades")
        
        count = c.fetchone()[0]
        print(f"   交易记录总数: {count}")
        
        if count == 0:
            print("   ⚠️ 数据库中没有交易记录")
            conn.close()
            return False
        
        # 检查数据质量
        if os.getenv('DB_TYPE', 'sqlite').lower() == 'mysql':
            c.execute("SELECT action, price, amount FROM trades WHERE price IS NULL OR amount IS NULL OR price = 0 OR amount = 0")
        else:
            c.execute("SELECT action, price, amount FROM trades WHERE price IS NULL OR amount IS NULL OR price = 0 OR amount = 0")
        
        invalid_records = c.fetchall()
        print(f"   无效记录数量: {len(invalid_records)}")
        
        if invalid_records:
            print("   ⚠️ 发现无效记录:")
            for i, record in enumerate(invalid_records[:5]):  # 只显示前5条
                print(f"      {i+1}. action={record[0]}, price={record[1]}, amount={record[2]}")
        
        conn.close()
        
        # 测试胜率计算
        stats = compute_win_rate_from_db()
        print(f"   本地计算结果:")
        print(f"      胜率: {stats.get('win_rate', 0)}%")
        print(f"      总交易: {stats.get('total_trades', 0)}")
        print(f"      总盈亏: ${stats.get('total_profit', 0):.2f}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 本地数据库检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_production_api():
    """检查生产环境API"""
    print("\n🔍 3. 检查生产环境API...")
    
    try:
        # 检查API端点
        url = "https://arena.aimaventop.com/api/dashboard"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"   ❌ API请求失败: {response.status_code}")
            return False
        
        data = response.json()
        performance = data.get('performance', {})
        
        print(f"   API返回数据:")
        print(f"      胜率: {performance.get('win_rate', 'N/A')}")
        print(f"      总交易: {performance.get('total_trades', 'N/A')}")
        print(f"      总盈亏: {performance.get('total_profit', 'N/A')}")
        
        # 检查是否为问题状态
        win_rate = performance.get('win_rate', 0)
        total_profit = performance.get('total_profit', 0)
        
        if win_rate == 100 and total_profit == 0:
            print("   ❌ 确认问题：胜率100%但盈亏为0")
            return False
        elif win_rate == 0 and total_profit == 0:
            print("   ⚠️ 可能问题：胜率和盈亏都为0")
            return False
        else:
            print("   ✅ API数据看起来正常")
            return True
            
    except Exception as e:
        print(f"   ❌ 生产环境API检查失败: {e}")
        return False

def check_vps_files():
    """检查VPS文件同步状态"""
    print("\n🔍 4. 检查VPS文件同步状态...")
    
    # 这里我们无法直接访问VPS，但可以检查本地修复文件
    fix_files = [
        'fix_profit_calculation.py',
        'restart_vps_server.sh',
        'sync_vps_data.py'
    ]
    
    for file_name in fix_files:
        file_path = os.path.join(os.path.dirname(__file__), file_name)
        if os.path.exists(file_path):
            print(f"   ✅ {file_name} 存在")
        else:
            print(f"   ❌ {file_name} 不存在")
    
    print("   ⚠️ 无法直接验证VPS文件同步状态")
    print("   建议手动检查VPS上的paper_trading.py是否包含修复代码")
    
    return True

def analyze_problem():
    """分析问题原因"""
    print("\n📊 5. 问题分析...")
    
    print("   根据检查结果，可能的问题原因：")
    print("   1. VPS上的paper_trading.py文件未正确更新修复代码")
    print("   2. VPS上的web_server.py进程未重启，仍在使用旧代码")
    print("   3. 数据库中存在大量price/amount为NULL或0的记录")
    print("   4. 环境变量配置问题导致连接错误的数据库")
    print("   5. 缓存问题导致前端显示旧数据")

def provide_solutions():
    """提供解决方案"""
    print("\n🔧 6. 解决方案...")
    
    print("   立即执行的步骤：")
    print("   1. 确认VPS上paper_trading.py包含修复代码（检查是否有'跳过无效记录'）")
    print("   2. 重启VPS上的web_server.py进程")
    print("   3. 清理浏览器缓存并刷新页面")
    print("   4. 检查VPS数据库连接配置")
    
    print("\n   手动验证命令：")
    print("   # 在VPS上执行：")
    print("   grep -n '跳过无效记录' paper_trading.py")
    print("   pkill -f web_server.py")
    print("   nohup python3 web_server.py > web_server.log 2>&1 &")
    print("   curl http://localhost:8080/api/dashboard")

def main():
    """主函数"""
    print("="*60)
    print("🔍 Alpha Arena 生产环境问题综合诊断")
    print("="*60)
    
    # 执行检查
    local_env_ok = check_local_environment()
    local_db_ok = check_local_database()
    prod_api_ok = check_production_api()
    vps_files_ok = check_vps_files()
    
    # 分析和建议
    analyze_problem()
    provide_solutions()
    
    print("\n" + "="*60)
    print("📋 诊断总结:")
    print(f"   本地环境: {'✅' if local_env_ok else '❌'}")
    print(f"   本地数据库: {'✅' if local_db_ok else '❌'}")
    print(f"   生产API: {'✅' if prod_api_ok else '❌'}")
    print(f"   VPS文件: {'✅' if vps_files_ok else '❌'}")
    print("="*60)

if __name__ == "__main__":
    main()