#!/bin/bash

echo "🚀 智能端口启动Web服务器"
echo "========================"

# 要尝试的端口列表
PORTS=(8080 8081 8082 9000 9001 3000 5000)

echo "🔍 寻找可用端口..."

for PORT in "${PORTS[@]}"; do
    # 检查端口是否被占用
    if ! lsof -i:$PORT >/dev/null 2>&1; then
        echo "✅ 找到可用端口: $PORT"
        echo ""
        echo "🌐 启动Web服务器在端口 $PORT..."
        echo "访问地址: http://localhost:$PORT"
        echo "外网访问: http://你的VPS_IP:$PORT"
        echo ""
        echo "按 Ctrl+C 停止服务器"
        echo "================================"
        
        # 设置端口环境变量并启动服务器
        export PORT=$PORT
        python3 web_server.py
        exit 0
    else
        echo "⚠️ 端口 $PORT 已被占用"
    fi
done

echo ""
echo "❌ 所有常用端口都被占用！"
echo ""
echo "🛠️ 解决方案:"
echo "1. 运行 ./fix_port_8080.sh 释放端口8080"
echo "2. 手动指定端口: PORT=端口号 python3 web_server.py"
echo "3. 检查防火墙设置确保端口开放"