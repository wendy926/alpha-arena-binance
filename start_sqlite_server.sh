#!/bin/bash

echo "🚀 启动Alpha Arena交易机器人（SQLite版本）"
echo "=" * 50

# 设置工作目录
cd "$(dirname "$0")"

# 创建数据目录
echo "📁 创建数据目录..."
mkdir -p data

# 初始化SQLite数据库
echo "🔄 初始化SQLite数据库..."
python3 init_sqlite.py

# 检查初始化结果
if [ $? -eq 0 ]; then
    echo "✅ SQLite数据库初始化成功"
else
    echo "❌ SQLite数据库初始化失败"
    exit 1
fi

# 启动web服务器
echo "🌐 启动Web服务器..."
echo "访问地址: http://localhost:8080"
echo "按 Ctrl+C 停止服务器"
echo ""

python3 web_server.py