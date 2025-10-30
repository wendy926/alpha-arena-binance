#!/bin/bash

echo "🚀 快速修复VPS Python包问题"
echo "============================================================"

# 安装必需的Python包
echo "📦 安装openai包..."
pip3 install openai

echo "📦 安装ccxt包..."
pip3 install ccxt

echo "📦 安装其他依赖..."
pip3 install python-dotenv requests flask flask-cors schedule

# 快速验证
echo "✅ 验证安装结果..."
python3 -c "
import sys
packages = ['openai', 'ccxt', 'requests', 'flask', 'schedule']
for pkg in packages:
    try:
        __import__(pkg)
        print(f'✓ {pkg} 安装成功')
    except ImportError:
        print(f'❌ {pkg} 安装失败')
        sys.exit(1)
print('🎉 所有包安装成功！')
"

echo "============================================================"
echo "✅ 修复完成！现在可以重启服务器："
echo "   PORT=8081 python3 web_server.py"
echo "============================================================"