#!/bin/bash

# 强力端口清理脚本 - 处理顽固的端口占用问题
# Force Port Cleanup Script - Handle stubborn port occupation

PORT=${1:-8080}

echo "🚨 强力清理端口${PORT}..."
echo "================================"

# 方法1: 使用fuser强制终止 (如果可用)
cleanup_with_fuser() {
    if command -v fuser >/dev/null 2>&1; then
        echo "🔥 使用fuser强制终止端口${PORT}上的进程..."
        fuser -k ${PORT}/tcp 2>/dev/null
        sleep 2
        return 0
    fi
    return 1
}

# 方法2: 使用netstat + kill
cleanup_with_netstat() {
    if command -v netstat >/dev/null 2>&1; then
        echo "🔍 使用netstat查找并终止进程..."
        PIDS=$(netstat -tulpn 2>/dev/null | grep ":${PORT} " | awk '{print $7}' | cut -d'/' -f1 | grep -v '^$' | sort -u)
        if [ -n "$PIDS" ]; then
            for pid in $PIDS; do
                if [ "$pid" != "-" ] && [ "$pid" -gt 0 ] 2>/dev/null; then
                    echo "终止进程: $pid"
                    kill -9 $pid 2>/dev/null
                fi
            done
            sleep 2
            return 0
        fi
    fi
    return 1
}

# 方法3: 使用ss + kill
cleanup_with_ss() {
    if command -v ss >/dev/null 2>&1; then
        echo "🔍 使用ss查找并终止进程..."
        PIDS=$(ss -tulpn 2>/dev/null | grep ":${PORT} " | awk '{print $6}' | cut -d',' -f2 | cut -d'=' -f2 | grep -v '^$' | sort -u)
        if [ -n "$PIDS" ]; then
            for pid in $PIDS; do
                if [ "$pid" != "-" ] && [ "$pid" -gt 0 ] 2>/dev/null; then
                    echo "终止进程: $pid"
                    kill -9 $pid 2>/dev/null
                fi
            done
            sleep 2
            return 0
        fi
    fi
    return 1
}

# 方法4: 暴力搜索相关进程
cleanup_brute_force() {
    echo "💥 暴力搜索相关进程..."
    
    # 搜索可能的web服务器进程
    PATTERNS=(
        "web_server.py"
        "python.*${PORT}"
        "flask.*${PORT}"
        ":${PORT}"
        "gunicorn.*${PORT}"
        "uwsgi.*${PORT}"
    )
    
    for pattern in "${PATTERNS[@]}"; do
        echo "搜索模式: $pattern"
        PIDS=$(ps aux | grep -E "$pattern" | grep -v grep | awk '{print $2}')
        if [ -n "$PIDS" ]; then
            for pid in $PIDS; do
                echo "终止进程: $pid (匹配: $pattern)"
                kill -9 $pid 2>/dev/null
            done
        fi
    done
    
    sleep 3
}

# 检查端口是否被释放
check_port_free() {
    # 使用Python检查端口
    python3 -c "
import socket
import sys
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('127.0.0.1', ${PORT}))
    sock.close()
    if result == 0:
        sys.exit(1)  # 端口仍被占用
    else:
        sys.exit(0)  # 端口已释放
except:
    sys.exit(0)  # 假设端口已释放
" 2>/dev/null
    return $?
}

echo "开始清理流程..."
echo ""

# 执行清理步骤
CLEANED=0

# 步骤1: fuser
if cleanup_with_fuser; then
    if check_port_free; then
        echo "✅ 使用fuser成功清理端口${PORT}"
        CLEANED=1
    fi
fi

# 步骤2: netstat (如果fuser失败)
if [ $CLEANED -eq 0 ]; then
    if cleanup_with_netstat; then
        if check_port_free; then
            echo "✅ 使用netstat成功清理端口${PORT}"
            CLEANED=1
        fi
    fi
fi

# 步骤3: ss (如果netstat失败)
if [ $CLEANED -eq 0 ]; then
    if cleanup_with_ss; then
        if check_port_free; then
            echo "✅ 使用ss成功清理端口${PORT}"
            CLEANED=1
        fi
    fi
fi

# 步骤4: 暴力清理 (最后手段)
if [ $CLEANED -eq 0 ]; then
    cleanup_brute_force
    if check_port_free; then
        echo "✅ 暴力清理成功释放端口${PORT}"
        CLEANED=1
    fi
fi

echo ""
echo "================================"

# 最终检查
if check_port_free; then
    echo "🎉 端口${PORT}已成功释放！"
    echo ""
    echo "现在可以启动服务:"
    echo "python3 web_server.py"
    echo ""
    echo "或指定端口:"
    echo "PORT=${PORT} python3 web_server.py"
    exit 0
else
    echo "❌ 端口${PORT}仍被占用"
    echo ""
    echo "建议使用备用端口:"
    echo "PORT=8081 python3 web_server.py"
    echo "PORT=8082 python3 web_server.py"
    echo "PORT=9000 python3 web_server.py"
    echo ""
    echo "或使用智能启动脚本:"
    echo "./start_web_alternative.sh"
    exit 1
fi