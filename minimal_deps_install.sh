#!/bin/bash

echo "🚀 安装最小依赖集（兼容旧环境）"
echo "================================"

echo "安装基础Web服务依赖..."
pip3 install flask flask-cors requests python-dotenv

echo ""
echo "安装调度依赖..."
pip3 install schedule

echo ""
echo "尝试安装兼容版本的openai..."
# 安装较老但兼容的openai版本
pip3 install "openai==0.28.1" --no-deps

if [ $? -ne 0 ]; then
    echo "openai 0.28.1安装失败，尝试更老版本..."
    pip3 install "openai==0.27.8" --no-deps
fi

echo ""
echo "安装可选依赖..."
pip3 install pymysql urllib3

echo ""
echo "🔍 验证关键模块..."
python3 -c "
modules = ['flask', 'requests', 'schedule', 'openai']
for module in modules:
    try:
        __import__(module)
        print(f'✅ {module} 可用')
    except ImportError:
        print(f'❌ {module} 不可用')
"

echo ""
echo "✅ 最小依赖安装完成！"
echo ""
echo "现在可以运行:"
echo "python3 init_sqlite.py"
echo "python3 web_server.py"