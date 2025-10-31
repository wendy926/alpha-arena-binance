#!/usr/bin/env python3
"""
快速端口修复脚本 - Python 3.6兼容版本
用于快速解决端口占用问题并重启Docker服务
"""

import os
import subprocess
import time
from datetime import datetime

def run_command(cmd, timeout=30):
    """执行命令并返回结果 - Python 3.6兼容版本"""
    try:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            return process.returncode, stdout, stderr
        except subprocess.TimeoutExpired:
            process.kill()
            return -1, "", "Command timeout"
    except Exception as e:
        return -1, "", str(e)

def print_step(step, description):
    """打印步骤"""
    print(f"\n{'='*60}")
    print(f"🔧 步骤 {step}: {description}")
    print(f"{'='*60}")

def kill_port_processes():
    """杀死占用端口的进程"""
    print_step(1, "清理端口占用")
    
    ports = [8080, 3306]
    
    for port in ports:
        print(f"\n🔍 检查端口 {port}...")
        code, out, err = run_command(f"netstat -tunlp | grep {port}")
        
        if out:
            print(f"⚠️  端口 {port} 被占用:")
            print(out)
            
            # 提取PID并杀死进程
            lines = out.strip().split('\n')
            for line in lines:
                if 'LISTEN' in line:
                    parts = line.split()
                    if len(parts) >= 7:
                        pid_info = parts[6]
                        if '/' in pid_info:
                            pid = pid_info.split('/')[0]
                            print(f"🔫 杀死进程 PID: {pid}")
                            
                            # 先尝试优雅关闭
                            run_command(f"kill {pid}")
                            time.sleep(2)
                            
                            # 检查是否还在运行
                            code2, out2, err2 = run_command(f"ps -p {pid}")
                            if code2 == 0:
                                print(f"🔫 强制杀死进程 PID: {pid}")
                                run_command(f"kill -9 {pid}")
        else:
            print(f"✅ 端口 {port} 未被占用")
    
    print("\n⏳ 等待端口释放...")
    time.sleep(3)

def stop_docker_services():
    """停止Docker服务"""
    print_step(2, "停止Docker服务")
    
    # 停止docker-compose服务
    print("🛑 停止docker-compose服务...")
    code, out, err = run_command("docker-compose down")
    if code == 0:
        print("✅ docker-compose服务已停止")
    else:
        print(f"⚠️  停止docker-compose服务时出现问题: {err}")
    
    # 停止所有相关容器
    print("\n🛑 停止所有相关容器...")
    containers = ["alpha-arena-mysql", "btc-trading-bot"]
    
    for container in containers:
        code, out, err = run_command(f"docker stop {container} 2>/dev/null")
        if code == 0:
            print(f"✅ 容器 {container} 已停止")
        
        code, out, err = run_command(f"docker rm {container} 2>/dev/null")
        if code == 0:
            print(f"✅ 容器 {container} 已删除")

def clean_docker_cache():
    """清理Docker缓存"""
    print_step(3, "清理Docker缓存")
    
    # 清理未使用的容器
    print("🧹 清理未使用的容器...")
    run_command("docker container prune -f")
    
    # 清理未使用的镜像
    print("🧹 清理未使用的镜像...")
    run_command("docker image prune -f")
    
    # 清理未使用的网络
    print("🧹 清理未使用的网络...")
    run_command("docker network prune -f")
    
    print("✅ Docker缓存清理完成")

def check_docker_files():
    """检查Docker相关文件"""
    print_step(4, "检查Docker相关文件")
    
    files_to_check = [
        "docker-compose.yml",
        "Dockerfile",
        ".env",
        "requirements.txt"
    ]
    
    for file in files_to_check:
        if os.path.exists(file):
            print(f"✅ {file} 存在")
        else:
            print(f"❌ {file} 不存在")

def restart_docker_services():
    """重启Docker服务"""
    print_step(5, "重启Docker服务")
    
    # 首先只启动MySQL
    print("🚀 启动MySQL服务...")
    code, out, err = run_command("docker-compose up -d mysql")
    if code == 0:
        print("✅ MySQL服务启动命令执行成功")
    else:
        print(f"❌ MySQL服务启动失败: {err}")
        return False
    
    # 等待MySQL启动
    print("⏳ 等待MySQL初始化...")
    for i in range(30):
        code, out, err = run_command("docker-compose ps mysql")
        if "healthy" in out or "Up" in out:
            print("✅ MySQL服务运行正常")
            break
        time.sleep(2)
        print(f"⏳ 等待中... ({i+1}/30)")
    
    # 检查MySQL日志
    print("\n📋 检查MySQL日志:")
    code, out, err = run_command("docker logs alpha-arena-mysql --tail 10")
    if out:
        print(out)
    
    # 启动所有服务
    print("\n🚀 启动所有服务...")
    code, out, err = run_command("docker-compose up -d")
    if code == 0:
        print("✅ 所有服务启动命令执行成功")
    else:
        print(f"❌ 服务启动失败: {err}")
        return False
    
    return True

def check_final_status():
    """检查最终状态"""
    print_step(6, "检查服务状态")
    
    # 检查容器状态
    print("📊 容器状态:")
    code, out, err = run_command("docker-compose ps")
    if out:
        print(out)
    
    # 检查端口状态
    print("\n📊 端口状态:")
    for port in [8080, 3306]:
        code, out, err = run_command(f"netstat -tunlp | grep {port}")
        if out:
            print(f"端口 {port}: {out.strip()}")
        else:
            print(f"端口 {port}: 未被占用")
    
    # 检查服务健康状态
    print("\n🏥 服务健康检查:")
    code, out, err = run_command("docker-compose ps --format 'table {{.Name}}\t{{.Status}}\t{{.Ports}}'")
    if out:
        print(out)

def main():
    """主函数"""
    print("🚀 快速端口修复开始...")
    print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 执行修复步骤
        kill_port_processes()
        stop_docker_services()
        clean_docker_cache()
        check_docker_files()
        
        if restart_docker_services():
            check_final_status()
            print("\n🎉 修复完成！")
            print("📋 请检查上述服务状态，确认所有服务正常运行")
        else:
            print("\n❌ 修复过程中出现问题")
            print("📋 请查看错误信息并手动处理")
            
    except Exception as e:
        print(f"\n❌ 修复过程中出现异常: {e}")
        print("📋 请手动检查并修复问题")

if __name__ == "__main__":
    main()