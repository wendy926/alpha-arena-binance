#!/bin/bash

echo "🔍 检查端口8080占用情况..."
echo "================================"

# 检查端口8080是否被占用 - 兼容多种检查方法
get_port_pid() {
    local port=8080
    
    # 方法1: 尝试使用lsof
    if command -v lsof >/dev/null 2>&1; then
        echo "📡 使用lsof检查端口..."
        lsof -ti:$port 2>/dev/null
        return
    fi
    
    # 方法2: 尝试使用netstat
    if command -v netstat >/dev/null 2>&1; then
        echo "📡 使用netstat检查端口..."
        netstat -tuln 2>/dev/null | grep ":$port " | awk '{print "occupied"}'
        return
    fi
    
    # 方法3: 尝试使用ss
    if command -v ss >/dev/null 2>&1; then
        echo "📡 使用ss检查端口..."
        ss -tuln 2>/dev/null | grep ":$port " | awk '{print "occupied"}'
        return
    fi
    
    # 方法4: 使用Python检查
    echo "🐍 使用Python检查端口..."
    python3 -c "
import socket
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('127.0.0.1', $port))
    sock.close()
    if result == 0:
        print('occupied')
except:
    pass
" 2>/dev/null
}

PORT_CHECK_RESULT=$(get_port_pid)

if [ -z "$PORT_CHECK_RESULT" ]; then
    echo "✅ 端口8080未被占用，可以直接启动服务"
    echo ""
    echo "现在可以运行:"
    echo "python3 web_server.py"
else
    echo "⚠️ 端口8080被占用"
    
    # 如果结果是数字PID，显示进程详情
    if [[ "$PORT_CHECK_RESULT" =~ ^[0-9]+$ ]]; then
        echo "进程ID: $PORT_CHECK_RESULT"
        echo ""
        echo "进程详情:"
        ps -p $PORT_CHECK_RESULT -o pid,ppid,cmd --no-headers 2>/dev/null || echo "无法获取进程详情"
        PORT_PID=$PORT_CHECK_RESULT
    else
        echo "检测到端口被占用，但无法获取具体进程ID"
        PORT_PID=""
    fi
    
    echo ""
    echo "🛠️ 解决方案选择:"
    echo "1. 自动终止占用进程 (推荐)"
    echo "2. 使用其他端口启动服务"
    echo "3. 手动处理"
    echo ""
    
    read -p "请选择解决方案 (1/2/3): " choice
    
    case $choice in
        1)
            if [ -n "$PORT_PID" ]; then
                echo "正在终止进程 $PORT_PID..."
                kill -9 $PORT_PID 2>/dev/null
                sleep 2
            else
                echo "尝试终止可能的web_server.py进程..."
                pkill -f "web_server.py" 2>/dev/null
                pkill -f "python.*8080" 2>/dev/null
                sleep 2
            fi
            
            # 再次检查
            NEW_CHECK=$(get_port_pid)
            if [ -z "$NEW_CHECK" ]; then
                echo "✅ 端口8080已释放"
                echo ""
                echo "现在可以运行:"
                echo "python3 web_server.py"
            else
                echo "❌ 端口仍被占用，请尝试其他解决方案"
            fi
            ;;
        2)
            echo "🔄 使用备用端口启动服务..."
            echo ""
            echo "可用的备用端口启动命令:"
            echo "PORT=8081 python3 web_server.py"
            echo "PORT=8082 python3 web_server.py"
            echo "PORT=9000 python3 web_server.py"
            ;;
        3)
            echo "📋 手动处理指南:"
            echo ""
            echo "1. 查看占用进程:"
            echo "   netstat -tuln | grep :8080"
            echo "   ss -tuln | grep :8080"
            echo "   ps aux | grep web_server"
            echo ""
            echo "2. 终止进程:"
            if [ -n "$PORT_PID" ]; then
                echo "   kill -9 $PORT_PID"
            fi
            echo "   pkill -f web_server.py"
            echo "   pkill -f python.*8080"
            echo ""
            echo "3. 或者使用其他端口:"
            echo "   PORT=8081 python3 web_server.py"
            ;;
        *)
            echo "❌ 无效选择"
            ;;
    esac
fi

echo ""
echo "💡 提示:"
echo "- 如果是之前启动的web_server.py进程，可以直接终止"
echo "- 如果是系统重要进程，建议使用其他端口"
echo "- 可以通过环境变量PORT指定其他端口"