#!/bin/bash

echo "📦 安装Python依赖包..."

# 尝试使用pip3
if command -v pip3 &> /dev/null; then
    echo "使用pip3安装依赖..."
    pip3 install flask flask-cors requests pymysql
elif command -v pip &> /dev/null; then
    echo "使用pip安装依赖..."
    pip install flask flask-cors requests pymysql
else
    echo "❌ 未找到pip或pip3，请手动安装Python包管理器"
    exit 1
fi

echo "✅ 依赖安装完成"
echo ""
echo "现在可以运行:"
echo "python3 init_sqlite.py"
echo "python3 web_server.py"