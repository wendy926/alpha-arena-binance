#!/bin/bash

echo "🔧 修复SQLite数据库和依赖问题"
echo "=" * 50

# 设置工作目录
cd "$(dirname "$0")"

echo "步骤1: 安装Python依赖..."
pip3 install flask flask-cors requests pymysql

if [ $? -eq 0 ]; then
    echo "✅ Python依赖安装成功"
else
    echo "❌ Python依赖安装失败，尝试使用pip..."
    pip install flask flask-cors requests pymysql
fi

echo ""
echo "步骤2: 检查并修复SQLite数据库表结构..."
python3 check_db_schema.py

echo ""
echo "步骤3: 重新初始化SQLite数据库..."
python3 init_sqlite.py

if [ $? -eq 0 ]; then
    echo "✅ SQLite数据库初始化成功"
else
    echo "❌ SQLite数据库初始化失败"
    exit 1
fi

echo ""
echo "步骤4: 测试web服务器启动..."
echo "🌐 启动Web服务器（测试模式）..."
echo "访问地址: http://localhost:8080"
echo "按 Ctrl+C 停止服务器"
echo ""

# 启动web服务器
python3 web_server.py