#!/bin/bash

echo "🚀 安装Alpha Arena所有依赖"
echo "=========================="

# 设置工作目录
cd "$(dirname "$0")"

echo "📦 安装Python依赖包..."

# 基于requirements.txt的完整依赖列表
DEPS="ccxt openai pandas schedule python-dotenv requests urllib3 flask flask-cors pymysql"

# 首先尝试pip3
if command -v pip3 &> /dev/null; then
    echo "使用pip3安装依赖..."
    pip3 install $DEPS
    INSTALL_STATUS=$?
elif command -v pip &> /dev/null; then
    echo "使用pip安装依赖..."
    pip install $DEPS
    INSTALL_STATUS=$?
else
    echo "❌ 未找到pip或pip3，请手动安装Python包管理器"
    exit 1
fi

# 检查安装结果
if [ $INSTALL_STATUS -eq 0 ]; then
    echo "✅ 所有依赖安装成功"
else
    echo "⚠️ 部分依赖可能安装失败，尝试单独安装关键依赖..."
    
    # 关键依赖列表
    CRITICAL_DEPS="openai flask flask-cors requests schedule python-dotenv"
    
    echo "安装关键依赖: $CRITICAL_DEPS"
    if command -v pip3 &> /dev/null; then
        pip3 install $CRITICAL_DEPS
    else
        pip install $CRITICAL_DEPS
    fi
    
    # 可选依赖（可能在某些环境下安装失败）
    OPTIONAL_DEPS="ccxt pandas pymysql urllib3"
    echo "尝试安装可选依赖: $OPTIONAL_DEPS"
    if command -v pip3 &> /dev/null; then
        pip3 install $OPTIONAL_DEPS 2>/dev/null || echo "⚠️ 部分可选依赖安装失败，但不影响基本功能"
    else
        pip install $OPTIONAL_DEPS 2>/dev/null || echo "⚠️ 部分可选依赖安装失败，但不影响基本功能"
    fi
fi

echo ""
echo "🔍 验证关键模块..."

# 验证关键模块是否可以导入
python3 -c "
try:
    import openai
    print('✅ openai模块可用')
except ImportError:
    print('❌ openai模块不可用')

try:
    import flask
    print('✅ flask模块可用')
except ImportError:
    print('❌ flask模块不可用')

try:
    import schedule
    print('✅ schedule模块可用')
except ImportError:
    print('❌ schedule模块不可用')

try:
    import requests
    print('✅ requests模块可用')
except ImportError:
    print('❌ requests模块不可用')
"

echo ""
echo "🎉 依赖安装完成！"
echo ""
echo "现在可以运行:"
echo "1. python3 init_sqlite.py    # 初始化数据库"
echo "2. python3 web_server.py     # 启动web服务器"
echo ""
echo "访问地址: http://localhost:8080"