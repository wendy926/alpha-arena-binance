#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VPS直接诊断脚本
全面检查Docker、端口、服务状态和架构问题
在VPS上直接运行此脚本进行问题诊断
"""

import os
import sys
import subprocess
import json
import time
import socket
from datetime import datetime

def print_header(title):
    """打印标题"""
    print("\n" + "="*60)
    print(f"🔍 {title}")
    print("="*60)

def run_command(cmd, capture_output=True, timeout=30):
    """安全执行命令"""
    try:
        if isinstance(cmd, str):
            result = subprocess.run(cmd, shell=True, 
                                  stdout=subprocess.PIPE if capture_output else None,
                                  stderr=subprocess.PIPE if capture_output else None,
                                  universal_newlines=True, timeout=timeout)
        else:
            result = subprocess.run(cmd, 
                                  stdout=subprocess.PIPE if capture_output else None,
                                  stderr=subprocess.PIPE if capture_output else None,
                                  universal_newlines=True, timeout=timeout)
        return result
    except subprocess.TimeoutExpired:
        print(f"   ⚠️ 命令超时: {cmd}")
        return None
    except Exception as e:
        print(f"   ❌ 命令执行失败: {cmd}, 错误: {e}")
        return None

def check_system_info():
    """检查系统基本信息"""
    print_header("系统基本信息")
    
    # 系统信息
    result = run_command("uname -a")
    if result:
        print(f"   🖥️ 系统: {result.stdout.strip()}")
    
    # Python版本
    print(f"   🐍 Python版本: {sys.version}")
    
    # 当前用户和目录
    print(f"   👤 当前用户: {os.getenv('USER', 'unknown')}")
    print(f"   📁 当前目录: {os.getcwd()}")
    
    # 系统负载
    result = run_command("uptime")
    if result:
        print(f"   📊 系统负载: {result.stdout.strip()}")

def check_docker_status():
    """检查Docker状态"""
    print_header("Docker服务状态")
    
    # Docker服务状态
    result = run_command("systemctl is-active docker")
    if result:
        docker_status = result.stdout.strip()
        print(f"   🐳 Docker服务状态: {docker_status}")
        
        if docker_status == "active":
            print("   ✅ Docker服务正在运行")
        else:
            print("   ❌ Docker服务未运行")
            return False
    
    # Docker版本
    result = run_command("docker --version")
    if result:
        print(f"   📦 Docker版本: {result.stdout.strip()}")
    
    # Docker容器状态
    print("\n   📋 Docker容器状态:")
    result = run_command("docker ps -a --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}'")
    if result:
        print(result.stdout)
    
    # Docker Compose状态
    print("\n   🔧 Docker Compose状态:")
    result = run_command("docker-compose ps")
    if result:
        print(result.stdout)
    
    return True

def check_port_usage():
    """检查端口使用情况"""
    print_header("端口使用情况")
    
    ports_to_check = [8080, 3306, 80, 443]
    
    for port in ports_to_check:
        print(f"\n   🔌 检查端口 {port}:")
        
        # 使用lsof检查端口
        result = run_command(f"lsof -i:{port}")
        if result and result.stdout.strip():
            print(f"   ✅ 端口{port}被占用:")
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # 跳过标题行
                print(f"      {line}")
        else:
            print(f"   ⚪ 端口{port}未被占用")
        
        # 使用netstat检查端口
        result = run_command(f"netstat -tlnp | grep :{port}")
        if result and result.stdout.strip():
            print(f"   📡 netstat显示:")
            for line in result.stdout.strip().split('\n'):
                print(f"      {line}")

def check_web_services():
    """检查Web服务状态"""
    print_header("Web服务状态")
    
    # 检查Python进程
    print("   🐍 Python相关进程:")
    result = run_command("ps aux | grep python | grep -v grep")
    if result and result.stdout.strip():
        for line in result.stdout.strip().split('\n'):
            print(f"      {line}")
    else:
        print("   ⚪ 没有发现Python进程")
    
    # 检查web_server.py进程
    print("\n   🌐 web_server.py进程:")
    result = run_command("ps aux | grep web_server.py | grep -v grep")
    if result and result.stdout.strip():
        for line in result.stdout.strip().split('\n'):
            print(f"      ✅ {line}")
    else:
        print("   ❌ web_server.py未运行")
    
    # 检查deepseekok2.py进程
    print("\n   🤖 deepseekok2.py进程:")
    result = run_command("ps aux | grep deepseekok2.py | grep -v grep")
    if result and result.stdout.strip():
        for line in result.stdout.strip().split('\n'):
            print(f"      ✅ {line}")
    else:
        print("   ❌ deepseekok2.py未运行")

def check_api_endpoints():
    """检查API端点"""
    print_header("API端点检查")
    
    endpoints = [
        "http://localhost:8080/api/dashboard",
        "http://localhost:8080/api/health",
        "http://localhost:8080/"
    ]
    
    for endpoint in endpoints:
        print(f"\n   🔗 测试: {endpoint}")
        result = run_command(f"curl -s -w 'HTTP_CODE:%{{http_code}}' '{endpoint}' | head -200")
        if result:
            output = result.stdout.strip()
            if "HTTP_CODE:200" in output:
                print("   ✅ 响应正常")
                # 显示响应内容的前100个字符
                content = output.replace("HTTP_CODE:200", "").strip()
                if content:
                    print(f"   📄 响应内容: {content[:100]}...")
            else:
                print(f"   ❌ 响应异常: {output}")
        else:
            print("   ❌ 请求失败")

def check_database_status():
    """检查数据库状态"""
    print_header("数据库状态")
    
    # 检查SQLite数据库文件
    db_files = ["trading.db", "alpha_arena.db", "data.db"]
    for db_file in db_files:
        if os.path.exists(db_file):
            print(f"   ✅ 发现数据库文件: {db_file}")
            stat = os.stat(db_file)
            print(f"      大小: {stat.st_size} bytes")
            print(f"      修改时间: {datetime.fromtimestamp(stat.st_mtime)}")
        else:
            print(f"   ⚪ 数据库文件不存在: {db_file}")
    
    # 检查MySQL连接（如果使用Docker）
    print("\n   🗄️ MySQL连接测试:")
    result = run_command("docker exec alpha-arena-mysql mysql -u alpha -palpha_pwd_2025 -e 'SELECT 1;'")
    if result and result.returncode == 0:
        print("   ✅ MySQL连接正常")
    else:
        print("   ❌ MySQL连接失败")

def check_log_files():
    """检查日志文件"""
    print_header("日志文件检查")
    
    log_files = ["web_server.log", "deepseekok2.log", "error.log", "app.log"]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"\n   📄 日志文件: {log_file}")
            stat = os.stat(log_file)
            print(f"      大小: {stat.st_size} bytes")
            print(f"      修改时间: {datetime.fromtimestamp(stat.st_mtime)}")
            
            # 显示最后10行
            result = run_command(f"tail -10 {log_file}")
            if result and result.stdout.strip():
                print("      最后10行:")
                for line in result.stdout.strip().split('\n'):
                    print(f"        {line}")
        else:
            print(f"   ⚪ 日志文件不存在: {log_file}")

def check_environment_variables():
    """检查环境变量"""
    print_header("环境变量检查")
    
    important_vars = [
        "PORT", "WEB_PORT", "MYSQL_HOST", "MYSQL_PORT", 
        "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DB",
        "DEEPSEEK_API_KEY", "OKX_API_KEY", "PAPER_TRADING"
    ]
    
    # 检查.env文件
    if os.path.exists(".env"):
        print("   ✅ 发现.env文件")
        with open(".env", "r") as f:
            content = f.read()
            for var in important_vars:
                if var in content:
                    # 不显示敏感信息的完整值
                    if "KEY" in var or "PASSWORD" in var:
                        print(f"   🔑 {var}: [已设置]")
                    else:
                        lines = content.split('\n')
                        for line in lines:
                            if line.startswith(f"{var}="):
                                value = line.split('=', 1)[1]
                                print(f"   📝 {var}: {value}")
                                break
    else:
        print("   ❌ .env文件不存在")
    
    # 检查系统环境变量
    print("\n   🌍 系统环境变量:")
    for var in important_vars:
        value = os.getenv(var)
        if value:
            if "KEY" in var or "PASSWORD" in var:
                print(f"   🔑 {var}: [已设置]")
            else:
                print(f"   📝 {var}: {value}")

def analyze_problems():
    """分析问题并提供建议"""
    print_header("问题分析和建议")
    
    problems = []
    solutions = []
    
    # 检查端口冲突
    result = run_command("lsof -i:8080")
    if result and result.stdout.strip():
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:  # 有实际的进程占用
            problems.append("端口8080被占用")
            solutions.append("执行: lsof -ti:8080 | xargs kill -9")
    
    # 检查Docker容器状态
    result = run_command("docker ps --filter name=btc-trading-bot --format '{{.Status}}'")
    if result and "Up" in result.stdout:
        problems.append("Docker容器正在运行，可能与直接运行的服务冲突")
        solutions.append("停止Docker容器: docker-compose down")
    
    # 检查web_server.py进程
    result = run_command("ps aux | grep web_server.py | grep -v grep")
    if not result or not result.stdout.strip():
        problems.append("web_server.py未运行")
        solutions.append("启动web服务: python3 web_server.py")
    
    # 输出问题和解决方案
    if problems:
        print("   🚨 发现的问题:")
        for i, problem in enumerate(problems, 1):
            print(f"      {i}. {problem}")
        
        print("\n   💡 建议的解决方案:")
        for i, solution in enumerate(solutions, 1):
            print(f"      {i}. {solution}")
    else:
        print("   ✅ 未发现明显问题")
    
    # 提供完整的修复流程
    print("\n   🔧 完整修复流程:")
    print("      1. 停止所有冲突服务: docker-compose down")
    print("      2. 清理端口: lsof -ti:8080 | xargs kill -9")
    print("      3. 等待: sleep 3")
    print("      4. 启动服务: python3 web_server.py")
    print("      5. 测试API: curl http://localhost:8080/api/dashboard")

def main():
    """主函数"""
    print("🔍 VPS直接诊断脚本")
    print(f"⏰ 开始时间: {datetime.now()}")
    
    try:
        check_system_info()
        check_docker_status()
        check_port_usage()
        check_web_services()
        check_api_endpoints()
        check_database_status()
        check_log_files()
        check_environment_variables()
        analyze_problems()
        
        print_header("诊断完成")
        print("   ✅ 诊断脚本执行完成")
        print("   📋 请根据上述分析结果进行相应的修复操作")
        print(f"   ⏰ 结束时间: {datetime.now()}")
        
    except KeyboardInterrupt:
        print("\n   ⚠️ 诊断被用户中断")
    except Exception as e:
        print(f"\n   ❌ 诊断过程中出现错误: {e}")

if __name__ == "__main__":
    main()