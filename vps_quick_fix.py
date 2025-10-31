#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VPS快速修复脚本 - 直接在VPS上运行此脚本
用于修复盈亏计算问题
"""

import os
import sys
import subprocess
import time

def backup_file(file_path):
    """创建备份文件"""
    backup_path = f"{file_path}.backup_{int(time.time())}"
    try:
        with open(file_path, 'r', encoding='utf-8') as src:
            content = src.read()
        with open(backup_path, 'w', encoding='utf-8') as dst:
            dst.write(content)
        print(f"✅ 已创建备份: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        return False

def fix_paper_trading():
    """修复paper_trading.py文件"""
    file_path = 'paper_trading.py'
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    # 创建备份
    if not backup_file(file_path):
        return False
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经修复
    if '跳过无效记录' in content:
        print("✅ paper_trading.py已包含修复代码")
        return True
    
    # 查找需要修复的代码段
    old_code = '''    for t in trades:
        action = (t.get('action') or '').lower()
        price = float(t.get('price') or 0.0)
        amount = float(t.get('amount') or 0.0)'''
    
    # 修复后的代码
    new_code = '''    for t in trades:
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
            continue'''
    
    if old_code in content:
        # 替换代码
        new_content = content.replace(old_code, new_code)
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ 成功修复 paper_trading.py")
        return True
    else:
        print("❌ 未找到需要修复的代码段")
        return False

def stop_processes():
    """停止相关进程"""
    print("🛑 停止现有进程...")
    
    processes = ['web_server.py', 'deepseekok2.py']
    
    for process in processes:
        try:
            result = subprocess.run(['pkill', '-f', process], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ 已停止 {process}")
            else:
                print(f"   ⚠️ {process} 可能未运行")
        except Exception as e:
            print(f"   ❌ 停止 {process} 失败: {e}")

def start_web_server():
    """启动web服务器"""
    print("🚀 启动web服务器...")
    
    try:
        # 启动web_server.py
        subprocess.Popen(['nohup', 'python3', 'web_server.py'], 
                        stdout=open('web_server.log', 'w'),
                        stderr=subprocess.STDOUT)
        
        print("   ✅ web_server.py 已启动")
        print("   📄 日志文件: web_server.log")
        
        # 等待服务启动
        time.sleep(3)
        
        return True
    except Exception as e:
        print(f"   ❌ 启动失败: {e}")
        return False

def verify_fix():
    """验证修复结果"""
    print("🔍 验证修复结果...")
    
    try:
        import requests
        
        # 测试API端点
        response = requests.get('http://localhost:8080/api/dashboard', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            performance = data.get('performance', {})
            
            win_rate = performance.get('win_rate', 0)
            total_profit = performance.get('total_profit', 0)
            total_trades = performance.get('total_trades', 0)
            
            print(f"   API响应正常:")
            print(f"      胜率: {win_rate}%")
            print(f"      总交易: {total_trades}")
            print(f"      总盈亏: ${total_profit:.2f}")
            
            if win_rate == 100 and total_profit == 0:
                print("   ❌ 问题仍然存在")
                return False
            else:
                print("   ✅ 修复成功")
                return True
        else:
            print(f"   ❌ API请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 验证失败: {e}")
        return False

def main():
    """主函数"""
    print("="*50)
    print("🔧 VPS快速修复脚本")
    print("="*50)
    
    # 1. 修复代码
    if not fix_paper_trading():
        print("❌ 代码修复失败，退出")
        return
    
    # 2. 停止进程
    stop_processes()
    
    # 3. 启动服务
    if not start_web_server():
        print("❌ 服务启动失败，退出")
        return
    
    # 4. 验证修复
    if verify_fix():
        print("\n✅ 修复完成！请访问网站验证结果")
    else:
        print("\n❌ 修复可能未完全成功，请检查日志")
    
    print("\n📋 后续步骤:")
    print("1. 访问: https://arena.aimaventop.com/flow/")
    print("2. 检查胜率和盈亏数据")
    print("3. 如有问题，查看日志: tail -f web_server.log")
    print("="*50)

if __name__ == "__main__":
    main()