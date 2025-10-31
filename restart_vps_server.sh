#!/bin/bash

echo "🔄 重启VPS服务器脚本"
echo "========================"

VPS_IP="47.236.15.204"
VPS_USER="root"

echo "📡 连接到VPS: $VPS_IP"

# 重启服务器的命令
ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP << 'EOF'
echo "🔍 检查当前运行的Python进程..."
ps aux | grep python | grep -v grep

echo ""
echo "🛑 停止现有的web服务器..."
pkill -f "python.*web_server.py" || echo "没有找到运行中的web_server.py进程"
pkill -f "python.*deepseekok2.py" || echo "没有找到运行中的deepseekok2.py进程"

echo ""
echo "⏳ 等待进程完全停止..."
sleep 3

echo ""
echo "📂 进入项目目录..."
cd /root/alpha-arena-okx || { echo "❌ 项目目录不存在"; exit 1; }

echo ""
echo "🔄 启动web服务器..."
nohup python3 web_server.py > web_server.log 2>&1 &

echo ""
echo "⏳ 等待服务器启动..."
sleep 5

echo ""
echo "🔍 检查服务器状态..."
if ps aux | grep -v grep | grep "python.*web_server.py" > /dev/null; then
    echo "✅ Web服务器启动成功"
else
    echo "❌ Web服务器启动失败"
    echo "📋 查看日志:"
    tail -20 web_server.log
fi

echo ""
echo "🌐 检查端口8080..."
if netstat -tlnp | grep :8080 > /dev/null; then
    echo "✅ 端口8080正在监听"
else
    echo "❌ 端口8080未监听"
fi

echo ""
echo "🧪 测试API端点..."
curl -s http://localhost:8080/api/performance | head -100

echo ""
echo "========================"
echo "🎉 重启完成！"
EOF

echo ""
echo "💡 重启完成，请检查网站: https://arena.aimaventop.com/flow/"