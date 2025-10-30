#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的胜率问题修复脚本
1. 检查数据库连接和数据
2. 验证胜率计算逻辑
3. 测试API端点
4. 提供修复建议
"""

import os
import sys
import time
import requests
import subprocess
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

def check_database_connection():
    """检查数据库连接和数据"""
    print("\n🔍 检查数据库连接和数据...")
    
    try:
        from paper_trading import _get_db_conn, compute_win_rate_from_db
        
        # 测试连接
        conn = _get_db_conn()
        c = conn.cursor()
        
        # 检查记录数量
        c.execute("SELECT COUNT(*) FROM trades")
        count = c.fetchone()[0]
        print(f"   交易记录总数: {count}")
        
        if count == 0:
            print("⚠️ 数据库中没有交易记录，胜率显示为0是正常的")
            conn.close()
            return False, "no_trades"
        
        # 测试胜率计算
        stats = compute_win_rate_from_db()
        print(f"   数据库计算胜率: {stats.get('win_rate', 0)}%")
        print(f"   数据库总交易: {stats.get('total_trades', 0)}")
        print(f"   数据库总盈亏: ${stats.get('total_profit', 0):.2f}")
        
        conn.close()
        return True, stats
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)

def check_web_data():
    """检查web_data中的数据"""
    print("\n🔍 检查web_data中的数据...")
    
    try:
        import deepseekok2
        
        performance = deepseekok2.web_data.get('performance', {})
        print(f"   web_data胜率: {performance.get('win_rate', 'N/A')}")
        print(f"   web_data总交易: {performance.get('total_trades', 'N/A')}")
        print(f"   web_data总盈亏: ${performance.get('total_profit', 0):.2f}")
        
        return performance
        
    except Exception as e:
        print(f"❌ web_data检查失败: {e}")
        return None

def test_api_endpoint(port=8080, max_retries=3):
    """测试API端点"""
    print(f"\n🔍 测试API端点 (端口 {port})...")
    
    url = f"http://localhost:{port}/api/dashboard"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                performance = data.get('performance', {})
                
                print(f"✅ API调用成功 (尝试 {attempt + 1})")
                print(f"   API返回胜率: {performance.get('win_rate', 'N/A')}")
                print(f"   API返回总交易: {performance.get('total_trades', 'N/A')}")
                print(f"   API返回总盈亏: ${performance.get('total_profit', 0):.2f}")
                
                return data
            else:
                print(f"⚠️ API调用失败 (尝试 {attempt + 1}): {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"⚠️ 无法连接到服务器 (尝试 {attempt + 1})")
            if attempt < max_retries - 1:
                print("   等待5秒后重试...")
                time.sleep(5)
        except Exception as e:
            print(f"⚠️ API测试失败 (尝试 {attempt + 1}): {e}")
            
    print(f"❌ API测试失败，已尝试 {max_retries} 次")
    return None

def check_server_running(port=8080):
    """检查服务器是否运行"""
    try:
        response = requests.get(f"http://localhost:{port}/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def suggest_fixes(db_result, api_result):
    """根据检查结果提供修复建议"""
    print("\n" + "="*60)
    print("💡 修复建议:")
    print("="*60)
    
    db_success, db_data = db_result
    
    if not db_success:
        if db_data == "no_trades":
            print("1. 数据库中没有交易记录")
            print("   - 这是正常情况，胜率显示为0%")
            print("   - 等待交易机器人执行一些交易后胜率会更新")
        else:
            print("1. 数据库连接或计算失败")
            print("   - 检查数据库配置 (.env文件)")
            print("   - 确保数据库服务正在运行")
            print("   - 检查paper_trading.py中的compute_win_rate_from_db函数")
        return
    
    if not api_result:
        print("1. API端点无法访问")
        print("   - 确保web服务器正在运行")
        print("   - 检查端口8080是否被占用")
        print("   - 尝试重启服务器: python web_server.py")
        return
    
    # 对比数据库和API结果
    db_win_rate = db_data.get('win_rate', 0) if isinstance(db_data, dict) else 0
    api_win_rate = api_result.get('performance', {}).get('win_rate', 0)
    
    if db_win_rate == api_win_rate:
        if db_win_rate > 0:
            print("✅ 数据同步正常，胜率计算正确")
            print("   - 如果前端仍显示0%，请检查浏览器缓存")
            print("   - 尝试强制刷新页面 (Ctrl+F5 或 Cmd+Shift+R)")
        else:
            print("⚠️ 胜率为0%，可能原因:")
            print("   - 没有盈利的交易")
            print("   - 交易记录不完整")
            print("   - 胜率计算逻辑需要调整")
    else:
        print("❌ 数据不同步")
        print(f"   数据库胜率: {db_win_rate}%")
        print(f"   API返回胜率: {api_win_rate}%")
        print("   - 重启web服务器可能解决问题")
        print("   - 检查web_server.py中的异常处理")

def main():
    print("="*60)
    print("🔧 胜率问题完整修复脚本")
    print("="*60)
    
    # 1. 加载环境变量
    if not load_env():
        return
    
    # 2. 检查数据库
    db_result = check_database_connection()
    
    # 3. 检查web_data
    web_data = check_web_data()
    
    # 4. 检查服务器是否运行
    server_running = check_server_running()
    print(f"\n🔍 服务器状态: {'运行中' if server_running else '未运行'}")
    
    # 5. 测试API端点
    api_result = None
    if server_running:
        api_result = test_api_endpoint()
    else:
        print("⚠️ 服务器未运行，跳过API测试")
    
    # 6. 提供修复建议
    suggest_fixes(db_result, api_result)
    
    # 7. 总结
    print("\n" + "="*60)
    print("📋 检查总结:")
    print("="*60)
    
    db_success, db_data = db_result
    print(f"数据库连接: {'✅' if db_success else '❌'}")
    print(f"服务器运行: {'✅' if server_running else '❌'}")
    print(f"API响应: {'✅' if api_result else '❌'}")
    
    if db_success and isinstance(db_data, dict):
        print(f"数据库胜率: {db_data.get('win_rate', 0)}%")
    
    if api_result:
        api_win_rate = api_result.get('performance', {}).get('win_rate', 0)
        print(f"API胜率: {api_win_rate}%")
    
    print("="*60)

if __name__ == "__main__":
    main()