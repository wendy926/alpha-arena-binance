#!/bin/bash

echo "🔧 Python 3.6 兼容性修复脚本"
echo "============================================================"

# 检查Python版本
echo "📋 检查Python版本..."
python3 --version

# 卸载可能存在的不兼容openai版本
echo "🗑️ 清理旧版本..."
pip3 uninstall openai -y

# 安装Python 3.6兼容的openai版本
echo "📦 安装Python 3.6兼容的openai包..."
pip3 install "openai==0.28.1"

# 验证ccxt安装
echo "📦 验证ccxt安装..."
python3 -c "
try:
    import ccxt
    print('✓ ccxt包可用')
except ImportError:
    print('❌ ccxt包不可用，正在安装...')
    import subprocess
    subprocess.run(['pip3', 'install', 'ccxt'])
"

# 安装其他必需依赖
echo "📦 安装其他依赖..."
pip3 install requests flask flask-cors schedule python-dotenv

# 验证安装
echo "✅ 验证包安装..."
python3 -c "
import sys
print(f'Python版本: {sys.version}')

packages = {
    'openai': '0.28.1兼容版本',
    'ccxt': '交易所连接',
    'requests': 'HTTP请求',
    'flask': 'Web框架',
    'schedule': '定时任务'
}

all_success = True
for pkg, desc in packages.items():
    try:
        __import__(pkg)
        print(f'✓ {pkg} ({desc}) 安装成功')
    except ImportError as e:
        print(f'❌ {pkg} ({desc}) 安装失败: {e}')
        all_success = False

if all_success:
    print('🎉 所有包安装成功！')
else:
    print('❌ 部分包安装失败')
    sys.exit(1)
"

echo "============================================================"
echo "✅ Python 3.6兼容性修复完成！"
echo "============================================================"