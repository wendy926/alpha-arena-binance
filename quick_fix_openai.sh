#!/bin/bash

echo "🔧 快速安装openai模块"
echo "===================="

# 安装openai模块
echo "安装openai模块..."
if command -v pip3 &> /dev/null; then
    pip3 install openai
elif command -v pip &> /dev/null; then
    pip install openai
else
    echo "❌ 未找到pip，请手动安装"
    exit 1
fi

if [ $? -eq 0 ]; then
    echo "✅ openai模块安装成功"
    
    # 验证安装
    python3 -c "import openai; print('✅ openai模块验证成功')" 2>/dev/null || echo "⚠️ openai模块验证失败"
    
    echo ""
    echo "现在可以启动web服务器:"
    echo "python3 web_server.py"
else
    echo "❌ openai模块安装失败"
    echo "请手动运行: pip3 install openai"
fi