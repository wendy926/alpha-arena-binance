#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VPS Docker架构完整修复方案
解决Docker容器内的服务问题
"""

import os
import sys
import subprocess
import time
import requests
import json
from datetime import datetime

def run_command(cmd, capture_output=True, timeout=30):
    """运行命令（兼容Python 3.6）"""
    try:
        if sys.version_info >= (3, 7):
            result = subprocess.run(cmd, shell=True, capture_output=capture_output, 
                                  text=True, timeout=timeout)
        else:
            # Python 3.6兼容
            result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE, universal_newlines=True, timeout=timeout)
        return result
    except subprocess.TimeoutExpired:
        print(f"⏰ 命令超时: {cmd}")
        return None
    except Exception as e:
        print(f"❌ 命令执行失败: {e}")
        return None

def check_docker_status():
    """检查Docker状态"""
    print("🐳 检查Docker状态...")
    
    # 检查Docker是否安装
    result = run_command("docker --version")
    if result and result.returncode == 0:
        print(f"✅ Docker已安装: {result.stdout.strip()}")
    else:
        print("❌ Docker未安装或不可用")
        return False
    
    # 检查Docker Compose
    result = run_command("docker-compose --version")
    if result and result.returncode == 0:
        print(f"✅ Docker Compose可用: {result.stdout.strip()}")
    else:
        print("❌ Docker Compose不可用")
        return False
    
    # 检查当前运行的容器
    result = run_command("docker ps")
    if result and result.returncode == 0:
        print("📋 当前运行的容器:")
        print(result.stdout)
    
    return True

def stop_all_services():
    """停止所有服务"""
    print("🛑 停止所有服务...")
    
    # 1. 停止Docker容器
    print("停止Docker容器...")
    run_command("docker-compose down", timeout=60)
    
    # 2. 杀死占用端口的进程
    ports = [8080, 3306]
    for port in ports:
        print(f"检查端口 {port}...")
        result = run_command(f"lsof -ti:{port}")
        if result and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    print(f"杀死进程 {pid} (端口 {port})")
                    run_command(f"kill -9 {pid}")
    
    # 3. 等待清理完成
    print("⏳ 等待服务停止...")
    time.sleep(5)

def backup_and_fix_files():
    """备份并修复文件"""
    print("📁 备份并修复文件...")
    
    # 备份paper_trading.py
    if os.path.exists("paper_trading.py"):
        backup_name = f"paper_trading_backup_{int(time.time())}.py"
        run_command(f"cp paper_trading.py {backup_name}")
        print(f"✅ 已备份 paper_trading.py -> {backup_name}")
    
    # 修复paper_trading.py中的胜率计算问题
    fix_code = '''
def compute_win_rate_from_db():
    """从数据库计算胜率和盈亏"""
    try:
        trades = get_all_trades()
        if not trades:
            return {
                'win_rate': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'total_profit': 0.0,
                'avg_profit_per_trade': 0.0
            }
        
        total_trades = len(trades)
        winning_trades = 0
        total_profit = 0.0
        
        for trade in trades:
            # 跳过无效的交易记录
            if not trade.get('price') or not trade.get('amount'):
                continue
            if trade.get('price') == 0 or trade.get('amount') == 0:
                continue
                
            profit = float(trade.get('profit', 0))
            total_profit += profit
            
            if profit > 0:
                winning_trades += 1
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
        avg_profit = total_profit / total_trades if total_trades > 0 else 0.0
        
        return {
            'win_rate': round(win_rate, 2),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'total_profit': round(total_profit, 2),
            'avg_profit_per_trade': round(avg_profit, 2)
        }
        
    except Exception as e:
        print(f"计算胜率时出错: {e}")
        return {
            'win_rate': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'total_profit': 0.0,
            'avg_profit_per_trade': 0.0
        }
'''
    
    # 应用修复
    if os.path.exists("paper_trading.py"):
        with open("paper_trading.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # 查找并替换compute_win_rate_from_db函数
        import re
        pattern = r'def compute_win_rate_from_db\(\):.*?(?=\ndef|\nclass|\n[a-zA-Z_]|\Z)'
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, fix_code.strip(), content, flags=re.DOTALL)
            
            with open("paper_trading.py", "w", encoding="utf-8") as f:
                f.write(content)
            print("✅ 已修复 paper_trading.py 中的胜率计算问题")
        else:
            print("⚠️ 未找到 compute_win_rate_from_db 函数，跳过修复")

def rebuild_docker_containers():
    """重新构建Docker容器"""
    print("🔨 重新构建Docker容器...")
    
    # 1. 清理旧容器和镜像
    print("清理旧容器...")
    run_command("docker-compose down --volumes --remove-orphans", timeout=60)
    
    # 2. 重新构建
    print("重新构建容器...")
    result = run_command("docker-compose build --no-cache", timeout=300)
    if result and result.returncode == 0:
        print("✅ 容器构建成功")
    else:
        print("❌ 容器构建失败")
        return False
    
    return True

def start_docker_services():
    """启动Docker服务"""
    print("🚀 启动Docker服务...")
    
    # 启动服务
    result = run_command("docker-compose up -d", timeout=120)
    if result and result.returncode == 0:
        print("✅ Docker服务启动成功")
    else:
        print("❌ Docker服务启动失败")
        return False
    
    # 等待服务启动
    print("⏳ 等待服务启动...")
    time.sleep(30)
    
    return True

def check_service_health():
    """检查服务健康状态"""
    print("🏥 检查服务健康状态...")
    
    # 检查容器状态
    result = run_command("docker-compose ps")
    if result:
        print("📋 容器状态:")
        print(result.stdout)
    
    # 检查端口
    ports = [8080, 3306]
    for port in ports:
        result = run_command(f"netstat -tlnp | grep :{port}")
        if result and result.stdout:
            print(f"✅ 端口 {port} 正在监听")
        else:
            print(f"❌ 端口 {port} 未监听")
    
    # 测试API
    print("🔗 测试API连接...")
    try:
        response = requests.get("http://localhost:8080/api/dashboard", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ API连接成功")
            print(f"胜率: {data.get('win_rate', 'N/A')}%")
            print(f"总利润: ${data.get('total_profit', 'N/A')}")
            
            # 检查是否还是100%胜率和0利润
            if data.get('win_rate') == 100 and data.get('total_profit') == 0:
                print("⚠️ 仍然显示100%胜率和0利润，可能需要进一步检查")
            else:
                print("✅ 胜率和利润数据看起来正常")
        else:
            print(f"❌ API返回错误状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ API连接失败: {e}")

def check_logs():
    """检查日志"""
    print("📋 检查容器日志...")
    
    # 检查主容器日志
    result = run_command("docker-compose logs --tail=20 btc-trading-bot")
    if result:
        print("🔍 btc-trading-bot 容器日志:")
        print(result.stdout)
    
    # 检查MySQL日志
    result = run_command("docker-compose logs --tail=10 mysql")
    if result:
        print("🔍 MySQL 容器日志:")
        print(result.stdout)

def main():
    """主函数"""
    print("🚀 VPS Docker架构完整修复开始...")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        # 1. 检查Docker状态
        if not check_docker_status():
            print("❌ Docker环境检查失败，请先安装Docker")
            return
        
        # 2. 停止所有服务
        stop_all_services()
        
        # 3. 备份并修复文件
        backup_and_fix_files()
        
        # 4. 重新构建容器
        if not rebuild_docker_containers():
            print("❌ 容器构建失败")
            return
        
        # 5. 启动服务
        if not start_docker_services():
            print("❌ 服务启动失败")
            return
        
        # 6. 检查健康状态
        check_service_health()
        
        # 7. 检查日志
        check_logs()
        
        print("=" * 50)
        print("✅ VPS Docker修复完成！")
        print("🌐 请访问: http://your-vps-ip:8080")
        print("📊 API测试: http://your-vps-ip:8080/api/dashboard")
        
    except Exception as e:
        print(f"❌ 修复过程中出现错误: {e}")
        print("请检查错误信息并重试")

if __name__ == "__main__":
    main()