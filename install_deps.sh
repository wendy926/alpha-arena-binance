#!/bin/bash

echo "📦 安装Python依赖包..."

# 完整的依赖列表（基于requirements.txt）
DEPS="ccxt openai pandas schedule python-dotenv requests urllib3 flask flask-cors pymysql"

# 尝试使用pip3
if command -v pip3 &> /dev/null; then
    echo "使用pip3安装依赖..."
    pip3 install $DEPS
elif command -v pip &> /dev/null; then
    echo "使用pip安装依赖..."
    pip install $DEPS
else
    echo "❌ 未找到pip或pip3，请手动安装Python包管理器"
    exit 1
fi

if [ $? -eq 0 ]; then
    echo "✅ 依赖安装完成"
else
    echo "⚠️ 部分依赖可能安装失败，尝试单独安装关键依赖..."
    # 安装关键依赖
    CRITICAL_DEPS="flask flask-cors requests schedule python-dotenv"
    if command -v pip3 &> /dev/null; then
        pip3 install $CRITICAL_DEPS
    else
        pip install $CRITICAL_DEPS
    fi
fi

echo ""
echo "现在可以运行:"
echo "python3 init_sqlite.py"
echo "python3 web_server.py"