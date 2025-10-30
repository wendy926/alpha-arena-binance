#!/bin/bash
# 安全启动服务器脚本 - 自动尝试可用端口

echo "🚀 安全启动Alpha Arena服务器..."

# 1. 停止现有进程
echo "============================================================"
echo "🛑 停止现有进程..."
pkill -f "web_server.py" 2>/dev/null || true
pkill -f "deepseekok2.py" 2>/dev/null || true
ps aux | grep -E "(web_server|deepseekok2)" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

echo "⏳ 等待进程停止..."
sleep 2

# 2. 尝试启动服务器
echo "============================================================"
echo "🌐 尝试启动Web服务器..."

# 端口列表
PORTS=(8081 8082 8083 8084 8085 8089 8090 8091 8092)

for port in "${PORTS[@]}"; do
    echo ""
    echo "🔍 尝试端口 $port..."
    
    # 测试端口是否可用
    if python3 -c "
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', $port))
    s.close()
    exit(0)
except:
    exit(1)
" 2>/dev/null; then
        echo "✅ 端口 $port 可用，启动服务器..."
        
        # 启动服务器
        echo "PORT=$port python3 web_server.py"
        echo ""
        echo "🌐 访问地址: http://your-server-ip:$port"
        echo "🌐 本地访问: http://localhost:$port"
        echo ""
        echo "🎯 服务器将在端口 $port 启动..."
        echo "============================================================"
        
        # 实际启动
        PORT=$port python3 web_server.py
        break
    else
        echo "❌ 端口 $port 被占用，尝试下一个..."
    fi
done

echo ""
echo "❌ 所有端口都被占用，请手动检查系统状态"
echo "============================================================"