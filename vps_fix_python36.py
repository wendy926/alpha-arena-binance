#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VPS修复脚本 - Python 3.6兼容版本
解决端口占用和进程管理问题
"""

import os
import sys
import subprocess
import time
import signal

def find_and_kill_processes():
    """查找并强制终止相关进程"""
    print("🛑 查找并停止现有进程...")
    
    try:
        # 查找占用8080端口的进程
        result = subprocess.run(['lsof', '-ti:8080'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              universal_newlines=True)
        
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        print(f"   ✅ 已终止进程 PID: {pid}")
                        time.sleep(1)
                    except:
                        try:
                            os.kill(int(pid), signal.SIGKILL)
                            print(f"   ✅ 已强制终止进程 PID: {pid}")
                        except:
                            print(f"   ⚠️ 无法终止进程 PID: {pid}")
        
        # 额外查找python进程
        result = subprocess.run(['pgrep', '-f', 'web_server.py'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              universal_newlines=True)
        
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        print(f"   ✅ 已终止web_server进程 PID: {pid}")
                        time.sleep(1)
                    except:
                        pass
        
        # 等待进程完全退出
        time.sleep(3)
        print("   ✅ 进程清理完成")
        
    except Exception as e:
        print(f"   ⚠️ 进程清理过程中出现错误: {e}")

def check_port_available():
    """检查端口是否可用"""
    try:
        result = subprocess.run(['lsof', '-ti:8080'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              universal_newlines=True)
        
        if result.stdout.strip():
            print("   ❌ 端口8080仍被占用")
            return False
        else:
            print("   ✅ 端口8080可用")
            return True
    except:
        print("   ✅ 端口8080可用")
        return True

def start_web_server():
    """启动web服务器"""
    print("🚀 启动web服务器...")
    
    if not check_port_available():
        print("   ❌ 端口不可用，无法启动服务")
        return False
    
    try:
        # 启动web_server.py
        with open('web_server.log', 'w') as log_file:
            process = subprocess.Popen(['python3', 'web_server.py'], 
                                     stdout=log_file,
                                     stderr=subprocess.STDOUT)
        
        print(f"   ✅ web_server.py 已启动，PID: {process.pid}")
        print("   📄 日志文件: web_server.log")
        
        # 等待服务启动
        time.sleep(5)
        
        return True
    except Exception as e:
        print(f"   ❌ 启动失败: {e}")
        return False

def verify_fix():
    """验证修复结果"""
    print("🔍 验证修复结果...")
    
    # 等待服务完全启动
    time.sleep(3)
    
    try:
        # 使用curl测试API（避免requests依赖问题）
        result = subprocess.run(['curl', '-s', 'http://localhost:8080/api/dashboard'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              universal_newlines=True,
                              timeout=10)
        
        if result.returncode == 0 and result.stdout:
            print("   ✅ API响应正常")
            print(f"   📄 响应内容: {result.stdout[:200]}...")
            
            # 简单检查响应内容
            if '"win_rate"' in result.stdout and '"total_profit"' in result.stdout:
                print("   ✅ 数据格式正确")
                return True
            else:
                print("   ⚠️ 数据格式可能有问题")
                return False
        else:
            print(f"   ❌ API请求失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ 验证失败: {e}")
        return False

def check_database_records():
    """检查数据库记录"""
    print("🔍 检查数据库记录...")
    
    try:
        # 导入并检查数据库
        sys.path.insert(0, '.')
        from paper_trading import _get_db_conn, get_all_trades
        
        trades = get_all_trades()
        print(f"   📊 总交易记录: {len(trades)}")
        
        if trades:
            # 检查数据质量
            valid_trades = 0
            invalid_trades = 0
            
            for trade in trades:
                price = trade.get('price')
                amount = trade.get('amount')
                
                if price is None or amount is None or price == 0 or amount == 0:
                    invalid_trades += 1
                else:
                    valid_trades += 1
            
            print(f"   ✅ 有效记录: {valid_trades}")
            print(f"   ⚠️ 无效记录: {invalid_trades}")
            
            if invalid_trades > 0:
                print("   💡 发现无效记录，这可能是问题的根源")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 数据库检查失败: {e}")
        return False

def main():
    """主函数"""
    print("="*60)
    print("🔧 VPS修复脚本 - Python 3.6兼容版本")
    print("="*60)
    
    # 1. 检查数据库记录
    check_database_records()
    
    # 2. 强制停止进程
    find_and_kill_processes()
    
    # 3. 启动服务
    if start_web_server():
        print("✅ 服务启动成功")
    else:
        print("❌ 服务启动失败")
        return
    
    # 4. 验证修复
    if verify_fix():
        print("\n✅ 修复验证成功")
    else:
        print("\n⚠️ 修复验证未完全成功")
    
    print("\n📋 后续步骤:")
    print("1. 访问: https://arena.aimaventop.com/flow/")
    print("2. 检查胜率和盈亏数据")
    print("3. 如有问题，查看日志: tail -f web_server.log")
    print("4. 检查进程状态: ps aux | grep python")
    print("="*60)

if __name__ == "__main__":
    main()