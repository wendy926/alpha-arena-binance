#!/bin/bash

echo "🔧 修复SQLite数据库和依赖问题"
echo "=" * 50

# 设置工作目录
cd "$(dirname "$0")"

echo "步骤1: 安装Python依赖..."
# 完整的依赖列表
DEPS="ccxt openai pandas schedule python-dotenv requests urllib3 flask flask-cors pymysql"
pip3 install $DEPS

if [ $? -eq 0 ]; then
    echo "✅ Python依赖安装成功"
else
    echo "❌ Python依赖安装失败，尝试使用pip..."
    pip install $DEPS
    if [ $? -ne 0 ]; then
        echo "⚠️ 尝试安装关键依赖..."
        CRITICAL_DEPS="flask flask-cors requests schedule python-dotenv"
        pip3 install $CRITICAL_DEPS || pip install $CRITICAL_DEPS
    fi
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