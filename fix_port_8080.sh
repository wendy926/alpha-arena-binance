#!/bin/bash

echo "🔍 检查端口8080占用情况..."
echo "================================"

# 检查端口8080是否被占用
PORT_PID=$(lsof -ti:8080)

if [ -z "$PORT_PID" ]; then
    echo "✅ 端口8080未被占用，可以直接启动服务"
    echo ""
    echo "现在可以运行:"
    echo "python3 web_server.py"
else
    echo "⚠️ 端口8080被以下进程占用:"
    echo "进程ID: $PORT_PID"
    
    # 显示占用端口的进程详情
    echo ""
    echo "进程详情:"
    ps -p $PORT_PID -o pid,ppid,cmd --no-headers 2>/dev/null || echo "无法获取进程详情"
    
    echo ""
    echo "🛠️ 解决方案选择:"
    echo "1. 自动终止占用进程 (推荐)"
    echo "2. 使用其他端口启动服务"
    echo "3. 手动处理"
    echo ""
    
    read -p "请选择解决方案 (1/2/3): " choice
    
    case $choice in
        1)
            echo "正在终止进程 $PORT_PID..."
            kill -9 $PORT_PID
            sleep 2
            
            # 再次检查
            NEW_PID=$(lsof -ti:8080)
            if [ -z "$NEW_PID" ]; then
                echo "✅ 端口8080已释放"
                echo ""
                echo "现在可以运行:"
                echo "python3 web_server.py"
            else
                echo "❌ 端口仍被占用，请手动处理"
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
            echo "1. 查看占用进程: lsof -i:8080"
            echo "2. 终止进程: kill -9 $PORT_PID"
            echo "3. 或者使用其他端口: PORT=8081 python3 web_server.py"
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