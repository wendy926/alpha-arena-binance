#!/bin/bash
# 快速端口清理脚本 - 兼容版本（不依赖lsof）

echo "🔧 快速清理端口占用..."

# 1. 检查端口占用情况
echo "============================================================"
echo "📋 检查端口占用情况..."

check_port() {
    local port=$1
    echo "检查端口 $port："
    
    # 尝试使用netstat
    if command -v netstat >/dev/null 2>&1; then
        netstat -tlnp 2>/dev/null | grep ":$port " || echo "端口 $port 未被占用"
    # 尝试使用ss
    elif command -v ss >/dev/null 2>&1; then
        ss -tlnp 2>/dev/null | grep ":$port " || echo "端口 $port 未被占用"
    else
        echo "⚠️ 无法检查端口状态（netstat和ss都不可用）"
    fi
}

check_port 8080
check_port 8081
check_port 8089

# 2. 停止相关进程
echo "============================================================"
echo "🛑 停止相关进程..."

# 停止web_server.py进程
echo "停止web_server.py进程..."
pkill -f "web_server.py" 2>/dev/null || true
pkill -f "python3.*web_server" 2>/dev/null || true

# 停止deepseekok2.py进程
echo "停止deepseekok2.py进程..."
pkill -f "deepseekok2.py" 2>/dev/null || true

# 使用ps和grep查找并停止相关进程
echo "查找并停止相关Python进程..."
ps aux | grep -E "(web_server|deepseekok2)" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

# 3. 使用netstat或ss查找并清理端口
echo "============================================================"
echo "🧹 强制清理端口..."

kill_port_process() {
    local port=$1
    echo "清理端口 $port..."
    
    # 使用netstat查找进程
    if command -v netstat >/dev/null 2>&1; then
        local pids=$(netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1 | grep -E '^[0-9]+$')
        if [ -n "$pids" ]; then
            echo "发现占用端口 $port 的进程: $pids"
            echo "$pids" | xargs kill -9 2>/dev/null || true
        fi
    # 使用ss查找进程
    elif command -v ss >/dev/null 2>&1; then
        local pids=$(ss -tlnp 2>/dev/null | grep ":$port " | sed 's/.*pid=\([0-9]*\).*/\1/' | grep -E '^[0-9]+$')
        if [ -n "$pids" ]; then
            echo "发现占用端口 $port 的进程: $pids"
            echo "$pids" | xargs kill -9 2>/dev/null || true
        fi
    else
        echo "⚠️ 无法查找端口进程（netstat和ss都不可用）"
    fi
}

kill_port_process 8080
kill_port_process 8081
kill_port_process 8089

# 4. 等待端口释放
echo "============================================================"
echo "⏳ 等待端口释放..."
sleep 3

# 5. 再次检查端口状态
echo "============================================================"
echo "✅ 检查端口清理结果..."

check_port_final() {
    local port=$1
    echo "端口 $port 状态："
    
    if command -v netstat >/dev/null 2>&1; then
        if netstat -tlnp 2>/dev/null | grep ":$port " >/dev/null; then
            echo "❌ 端口 $port 仍被占用"
            netstat -tlnp 2>/dev/null | grep ":$port "
        else
            echo "✅ 端口 $port 已释放"
        fi
    elif command -v ss >/dev/null 2>&1; then
        if ss -tlnp 2>/dev/null | grep ":$port " >/dev/null; then
            echo "❌ 端口 $port 仍被占用"
            ss -tlnp 2>/dev/null | grep ":$port "
        else
            echo "✅ 端口 $port 已释放"
        fi
    else
        echo "⚠️ 无法检查端口状态"
    fi
}

check_port_final 8080
check_port_final 8081
check_port_final 8089

# 6. 测试端口可用性
echo "============================================================"
echo "🧪 测试端口可用性..."

test_port() {
    local port=$1
    echo "测试端口 $port..."
    
    # 尝试绑定端口
    if python3 -c "
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', $port))
    s.close()
    print('✅ 端口 $port 可用')
except Exception as e:
    print('❌ 端口 $port 不可用:', e)
" 2>/dev/null; then
        echo "端口 $port 测试完成"
    else
        echo "端口 $port 测试失败"
    fi
}

test_port 8080
test_port 8081
test_port 8089

# 7. 建议下一步操作
echo "============================================================"
echo "🚀 建议的启动命令："
echo ""
echo "选项1 - 使用端口8081："
echo "PORT=8081 python3 web_server.py"
echo ""
echo "选项2 - 使用端口8089："
echo "PORT=8089 python3 web_server.py"
echo ""
echo "选项3 - 使用端口8082："
echo "PORT=8082 python3 web_server.py"
echo ""
echo "🌐 访问地址将是："
echo "http://your-server-ip:PORT"
echo ""
echo "💡 如果仍有问题，可以尝试："
echo "1. 重启服务器: reboot"
echo "2. 检查防火墙设置"
echo "3. 使用其他端口如: 8090, 8091, 8092"
echo "============================================================"