#!/bin/bash

echo "🔧 快速安装缺失的schedule模块"
echo "================================"

# 安装schedule模块
echo "安装schedule模块..."
if command -v pip3 &> /dev/null; then
    pip3 install schedule
elif command -v pip &> /dev/null; then
    pip install schedule
else
    echo "❌ 未找到pip，请手动安装"
    exit 1
fi

if [ $? -eq 0 ]; then
    echo "✅ schedule模块安装成功"
    echo ""
    echo "现在可以启动web服务器:"
    echo "python3 web_server.py"
else
    echo "❌ schedule模块安装失败"
    echo "请手动运行: pip3 install schedule"
fi