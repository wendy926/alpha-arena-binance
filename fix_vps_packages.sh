#!/bin/bash

echo "============================================================"
echo "🔧 VPS Python包修复脚本"
echo "============================================================"

# 检查Python版本
echo "📋 检查Python环境..."
python3 --version
pip3 --version

# 更新pip到最新版本
echo "📦 更新pip..."
python3 -m pip install --upgrade pip

# 安装openai包（DeepSeek AI功能必需）
echo "🧠 安装openai包..."
pip3 install openai

# 安装ccxt包（交易所连接必需）
echo "💱 安装ccxt包..."
pip3 install ccxt

# 安装其他可能缺失的依赖
echo "📚 安装其他依赖..."
pip3 install requests flask flask-cors schedule python-dotenv

# 验证安装
echo "✅ 验证包安装..."
python3 -c "
try:
    import openai
    print('✓ openai包安装成功')
except ImportError as e:
    print('❌ openai包安装失败:', e)

try:
    import ccxt
    print('✓ ccxt包安装成功')
except ImportError as e:
    print('❌ ccxt包安装失败:', e)

try:
    import requests, flask, schedule
    print('✓ 其他依赖包安装成功')
except ImportError as e:
    print('❌ 其他依赖包安装失败:', e)
"

# 检查.env文件
echo "🔍 检查.env配置..."
if [ -f ".env" ]; then
    echo "✓ .env文件存在"
    if grep -q "DEEPSEEK_API_KEY" .env; then
        echo "✓ DEEPSEEK_API_KEY已配置"
        # 隐藏API密钥的敏感部分
        grep "DEEPSEEK_API_KEY" .env | sed 's/\(DEEPSEEK_API_KEY=sk-[a-zA-Z0-9]\{8\}\)[a-zA-Z0-9]*\([a-zA-Z0-9]\{8\}\)/\1****\2/'
    else
        echo "⚠️ DEEPSEEK_API_KEY未配置"
    fi
    
    if grep -q "AI_PROVIDER=deepseek" .env; then
        echo "✓ AI_PROVIDER已设置为deepseek"
    else
        echo "⚠️ 添加AI_PROVIDER=deepseek配置..."
        echo "AI_PROVIDER=deepseek" >> .env
    fi
else
    echo "❌ .env文件不存在，请创建并配置"
fi

# 测试DeepSeek连接
echo "🔗 测试DeepSeek连接..."
python3 -c "
import os
from dotenv import load_dotenv

load_dotenv()

try:
    from openai import OpenAI
    
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print('❌ DEEPSEEK_API_KEY未设置')
        exit(1)
    
    if not api_key.startswith('sk-'):
        print('❌ DEEPSEEK_API_KEY格式错误')
        exit(1)
    
    client = OpenAI(
        api_key=api_key,
        base_url='https://api.deepseek.com'
    )
    
    print('🔍 测试DeepSeek API连接...')
    response = client.chat.completions.create(
        model='deepseek-chat',
        messages=[{'role': 'user', 'content': 'Hello'}],
        max_tokens=10,
        timeout=10.0
    )
    
    if response and response.choices:
        print('✅ DeepSeek连接测试成功！')
    else:
        print('❌ DeepSeek连接测试失败：响应为空')
        
except Exception as e:
    print(f'❌ DeepSeek连接测试失败: {e}')
"

# 测试ccxt连接
echo "💱 测试ccxt连接..."
python3 -c "
try:
    import ccxt
    
    # 测试Binance连接（不需要API密钥的公开接口）
    exchange = ccxt.binance()
    ticker = exchange.fetch_ticker('BTC/USDT')
    print(f'✅ ccxt连接测试成功！BTC价格: \${ticker[\"last\"]:,.2f}')
    
except Exception as e:
    print(f'❌ ccxt连接测试失败: {e}')
"

echo "============================================================"
echo "🎉 VPS包修复完成！"
echo "============================================================"
echo ""
echo "📋 下一步操作："
echo "1. 确认DEEPSEEK_API_KEY已正确设置"
echo "2. 重启web服务器: PORT=8081 python3 web_server.py"
echo "3. 访问 http://your-vps-ip:8081 查看效果"
echo ""
echo "✅ 修复完成后应该看到："
echo "   - AI模型: DEEPSEEK (deepseek-chat) 已连接"
echo "   - 余额信息正常显示"
echo "   - AI决策功能正常工作"