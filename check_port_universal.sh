#!/bin/bash

# 通用端口检查脚本 - 兼容没有lsof的系统
# Universal Port Checker - Compatible with systems without lsof

PORT=${1:-8080}

echo "🔍 检查端口${PORT}占用情况..."
echo "================================"

# 检查是否有可用的端口检查工具
check_port_with_netstat() {
    if command -v netstat >/dev/null 2>&1; then
        echo "📡 使用netstat检查端口..."
        RESULT=$(netstat -tuln 2>/dev/null | grep ":${PORT} ")
        if [ -n "$RESULT" ]; then
            echo "❌ 端口${PORT}被占用:"
            echo "$RESULT"
            return 1
        else
            echo "✅ 端口${PORT}未被占用 (netstat检查)"
            return 0
        fi
    fi
    return 2
}

check_port_with_ss() {
    if command -v ss >/dev/null 2>&1; then
        echo "📡 使用ss检查端口..."
        RESULT=$(ss -tuln 2>/dev/null | grep ":${PORT} ")
        if [ -n "$RESULT" ]; then
            echo "❌ 端口${PORT}被占用:"
            echo "$RESULT"
            return 1
        else
            echo "✅ 端口${PORT}未被占用 (ss检查)"
            return 0
        fi
    fi
    return 2
}

check_port_with_python() {
    echo "🐍 使用Python检查端口..."
    python3 -c "
import socket
import sys

def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    except:
        return False

port = ${PORT}
if check_port(port):
    print(f'❌ 端口{port}被占用')
    sys.exit(1)
else:
    print(f'✅ 端口{port}未被占用 (Python检查)')
    sys.exit(0)
"
    return $?
}

# 尝试不同的检查方法
PORT_OCCUPIED=0

# 方法1: netstat
check_port_with_netstat
NETSTAT_RESULT=$?

if [ $NETSTAT_RESULT -eq 1 ]; then
    PORT_OCCUPIED=1
elif [ $NETSTAT_RESULT -eq 0 ]; then
    PORT_OCCUPIED=0
else
    # 方法2: ss
    check_port_with_ss
    SS_RESULT=$?
    
    if [ $SS_RESULT -eq 1 ]; then
        PORT_OCCUPIED=1
    elif [ $SS_RESULT -eq 0 ]; then
        PORT_OCCUPIED=0
    else
        # 方法3: Python
        check_port_with_python
        PYTHON_RESULT=$?
        
        if [ $PYTHON_RESULT -eq 1 ]; then
            PORT_OCCUPIED=1
        else
            PORT_OCCUPIED=0
        fi
    fi
fi

echo ""
echo "================================"

if [ $PORT_OCCUPIED -eq 1 ]; then
    echo "🚨 端口${PORT}被占用！"
    echo ""
    echo "解决方案:"
    echo "1. 使用其他端口启动服务:"
    echo "   PORT=8081 python3 web_server.py"
    echo "   PORT=8082 python3 web_server.py"
    echo "   PORT=9000 python3 web_server.py"
    echo ""
    echo "2. 或者尝试终止占用进程:"
    echo "   pkill -f web_server.py"
    echo "   pkill -f python.*8080"
    echo ""
    echo "3. 使用智能启动脚本:"
    echo "   ./start_web_alternative.sh"
    
    exit 1
else
    echo "✅ 端口${PORT}可用！"
    echo ""
    echo "现在可以启动服务:"
    echo "python3 web_server.py"
    echo ""
    echo "或指定端口:"
    echo "PORT=${PORT} python3 web_server.py"
    
    exit 0
fi