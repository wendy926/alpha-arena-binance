#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VPS自动修复脚本
基于诊断结果自动解决Docker代理端口冲突和服务架构问题
"""

import os
import sys
import subprocess
import time
import signal

def print_step(step, description):
    """打印步骤"""
    print(f"\n🔧 步骤{step}: {description}")
    print("-" * 50)

def run_command_safe(cmd, description="", timeout=30):
    """安全执行命令"""
    print(f"   执行: {cmd}")
    try:
        if isinstance(cmd, str):
            result = subprocess.run(cmd, shell=True, 
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  universal_newlines=True, 
                                  timeout=timeout)
        else:
            result = subprocess.run(cmd, 
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  universal_newlines=True, 
                                  timeout=timeout)
        
        if result.returncode == 0:
            print(f"   ✅ {description}成功")
            if result.stdout.strip():
                print(f"   📄 输出: {result.stdout.strip()}")
            return True
        else:
            print(f"   ⚠️ {description}失败")
            if result.stderr.strip():
                print(f"   ❌ 错误: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print(f"   ⚠️ {description}超时")
        return False
    except Exception as e:
        print(f"   ❌ {description}异常: {e}")
        return False

def stop_docker_services():
    """停止Docker服务"""
    print_step(1, "停止Docker服务")
    
    # 停止docker-compose服务
    if os.path.exists("docker-compose.yml"):
        run_command_safe("docker-compose down", "停止Docker Compose服务")
    
    # 停止特定容器
    containers = ["btc-trading-bot", "alpha-arena-mysql"]
    for container in containers:
        run_command_safe(f"docker stop {container}", f"停止容器{container}")
        run_command_safe(f"docker rm {container}", f"删除容器{container}")
    
    print("   ✅ Docker服务停止完成")

def kill_port_processes():
    """强制终止占用端口的进程"""
    print_step(2, "清理端口占用")
    
    ports = [8080, 3306]
    
    for port in ports:
        print(f"   🔌 清理端口{port}:")
        
        # 使用lsof查找并终止进程
        result = subprocess.run(f"lsof -ti:{port}", shell=True, 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              universal_newlines=True)
        
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        print(f"      ✅ 终止进程 PID: {pid}")
                        time.sleep(1)
                    except:
                        try:
                            os.kill(int(pid), signal.SIGKILL)
                            print(f"      ✅ 强制终止进程 PID: {pid}")
                        except:
                            print(f"      ⚠️ 无法终止进程 PID: {pid}")
        else:
            print(f"      ⚪ 端口{port}未被占用")
    
    # 额外清理Python进程
    run_command_safe("pkill -f web_server.py", "终止web_server.py进程")
    run_command_safe("pkill -f deepseekok2.py", "终止deepseekok2.py进程")
    
    print("   ✅ 端口清理完成")

def wait_for_cleanup():
    """等待清理完成"""
    print_step(3, "等待服务完全停止")
    
    for i in range(5, 0, -1):
        print(f"   ⏳ 等待 {i} 秒...")
        time.sleep(1)
    
    # 验证端口是否释放
    result = subprocess.run("lsof -i:8080", shell=True, 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE,
                          universal_newlines=True)
    
    if result.stdout.strip():
        print("   ⚠️ 端口8080仍被占用，尝试强制清理")
        run_command_safe("lsof -ti:8080 | xargs kill -9", "强制清理端口8080")
        time.sleep(2)
    else:
        print("   ✅ 端口8080已释放")

def check_environment():
    """检查环境配置"""
    print_step(4, "检查环境配置")
    
    # 检查必要文件
    required_files = ["web_server.py", "paper_trading.py", "deepseekok2.py"]
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ 文件存在: {file}")
        else:
            print(f"   ❌ 文件缺失: {file}")
            return False
    
    # 检查.env文件
    if os.path.exists(".env"):
        print("   ✅ .env文件存在")
    else:
        print("   ⚠️ .env文件不存在，将使用默认配置")
    
    # 检查Python版本
    print(f"   🐍 Python版本: {sys.version}")
    
    return True

def start_web_server():
    """启动Web服务器"""
    print_step(5, "启动Web服务器")
    
    # 设置环境变量
    os.environ['PORT'] = '8080'
    
    try:
        # 启动web_server.py
        print("   🚀 启动web_server.py...")
        with open('web_server.log', 'w') as log_file:
            process = subprocess.Popen(['python3', 'web_server.py'], 
                                     stdout=log_file,
                                     stderr=subprocess.STDOUT)
        
        print(f"   ✅ web_server.py已启动，PID: {process.pid}")
        print("   📄 日志文件: web_server.log")
        
        # 等待服务启动
        print("   ⏳ 等待服务启动...")
        time.sleep(5)
        
        return True
    except Exception as e:
        print(f"   ❌ 启动失败: {e}")
        return False

def verify_services():
    """验证服务状态"""
    print_step(6, "验证服务状态")
    
    # 检查进程
    result = subprocess.run("ps aux | grep web_server.py | grep -v grep", 
                          shell=True, stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, universal_newlines=True)
    
    if result.stdout.strip():
        print("   ✅ web_server.py进程正在运行")
        print(f"   📋 进程信息: {result.stdout.strip()}")
    else:
        print("   ❌ web_server.py进程未运行")
        return False
    
    # 检查端口
    result = subprocess.run("lsof -i:8080", shell=True, 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, universal_newlines=True)
    
    if result.stdout.strip():
        print("   ✅ 端口8080正在监听")
    else:
        print("   ❌ 端口8080未监听")
        return False
    
    # 测试API
    print("   🔗 测试API端点...")
    time.sleep(2)  # 额外等待
    
    result = subprocess.run("curl -s -w 'HTTP_CODE:%{http_code}' http://localhost:8080/api/dashboard", 
                          shell=True, stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, universal_newlines=True)
    
    if result.stdout and "HTTP_CODE:200" in result.stdout:
        print("   ✅ API响应正常")
        # 显示响应内容
        content = result.stdout.replace("HTTP_CODE:200", "").strip()
        if content:
            print(f"   📄 API响应: {content[:100]}...")
        return True
    else:
        print("   ❌ API响应异常")
        if result.stdout:
            print(f"   📄 响应: {result.stdout}")
        return False

def show_final_status():
    """显示最终状态"""
    print_step(7, "修复完成")
    
    print("   🎉 自动修复流程完成！")
    print("\n   📋 后续步骤:")
    print("   1. 访问: https://arena.aimaventop.com/flow/")
    print("   2. 检查数据是否正常显示")
    print("   3. 如有问题，查看日志: tail -f web_server.log")
    print("   4. 检查进程状态: ps aux | grep python")
    
    print("\n   🔧 手动命令参考:")
    print("   - 查看日志: tail -20 web_server.log")
    print("   - 重启服务: pkill -f web_server.py && python3 web_server.py &")
    print("   - 检查端口: lsof -i:8080")
    print("   - 测试API: curl http://localhost:8080/api/dashboard")

def main():
    """主函数"""
    print("🔧 VPS自动修复脚本")
    print("=" * 60)
    print("⚠️  警告: 此脚本将停止Docker服务并重启Web服务")
    print("=" * 60)
    
    try:
        # 执行修复流程
        stop_docker_services()
        kill_port_processes()
        wait_for_cleanup()
        
        if not check_environment():
            print("❌ 环境检查失败，无法继续")
            return
        
        if start_web_server():
            time.sleep(3)  # 等待服务完全启动
            if verify_services():
                show_final_status()
            else:
                print("❌ 服务验证失败，请检查日志")
        else:
            print("❌ 服务启动失败")
    
    except KeyboardInterrupt:
        print("\n⚠️ 修复被用户中断")
    except Exception as e:
        print(f"\n❌ 修复过程中出现错误: {e}")

if __name__ == "__main__":
    main()