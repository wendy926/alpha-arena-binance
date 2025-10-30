#!/bin/bash
# Python 3.6 VPS修复脚本
# 解决openai包安装和AI功能问题

echo "🔧 开始修复Python 3.6环境..."

# 1. 检查Python版本
echo "============================================================"
echo "📋 检查Python版本..."
python3 --version

# 2. 升级pip
echo "============================================================"
echo "⬆️ 升级pip..."
python3 -m pip install --upgrade pip

# 3. 卸载可能存在的openai包
echo "============================================================"
echo "🗑️ 清理现有openai包..."
pip3 uninstall -y openai

# 4. 安装Python 3.6兼容的openai版本
echo "============================================================"
echo "📦 安装Python 3.6兼容的openai版本..."
pip3 install openai==0.28.1

# 5. 安装其他必需包
echo "============================================================"
echo "📦 安装其他必需包..."
pip3 install ccxt requests flask flask-cors schedule python-dotenv

# 6. 验证安装
echo "============================================================"
echo "✅ 验证包安装..."

# 检查openai
if python3 -c "import openai; print('openai版本:', openai.__version__)" 2>/dev/null; then
    echo "✅ openai 安装成功"
else
    echo "❌ openai 安装失败"
fi

# 检查ccxt
if python3 -c "import ccxt; print('ccxt版本:', ccxt.__version__)" 2>/dev/null; then
    echo "✅ ccxt 安装成功"
else
    echo "❌ ccxt 安装失败"
fi

# 检查其他包
for package in requests flask schedule python-dotenv; do
    if python3 -c "import $package" 2>/dev/null; then
        echo "✅ $package 安装成功"
    else
        echo "❌ $package 安装失败"
    fi
done

# 7. 检查.env文件
echo "============================================================"
echo "📋 检查.env配置..."
if [ -f ".env" ]; then
    echo "✅ .env文件存在"
    if grep -q "DEEPSEEK_API_KEY" .env; then
        echo "✅ DEEPSEEK_API_KEY已配置"
    else
        echo "❌ DEEPSEEK_API_KEY未配置"
        echo "请在.env文件中添加: DEEPSEEK_API_KEY=your_api_key"
    fi
    
    if grep -q "AI_PROVIDER=deepseek" .env; then
        echo "✅ AI_PROVIDER已配置"
    else
        echo "⚠️ 建议在.env文件中添加: AI_PROVIDER=deepseek"
    fi
else
    echo "❌ .env文件不存在"
    echo "请创建.env文件并添加必要配置"
fi

# 8. 测试DeepSeek连接（如果有API key）
echo "============================================================"
echo "🧪 测试DeepSeek连接..."

cat > test_deepseek_py36.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv未安装，跳过.env加载")

# 测试openai导入
try:
    import openai
    print(f"✅ openai导入成功，版本: {openai.__version__}")
    
    # 获取API key
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("❌ DEEPSEEK_API_KEY未设置")
        sys.exit(1)
    
    # 配置openai
    openai.api_key = api_key
    openai.api_base = "https://api.deepseek.com"
    
    # 测试连接
    print("🔍 测试DeepSeek API连接...")
    response = openai.ChatCompletion.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=10,
        temperature=0.1
    )
    
    content = response.choices[0].message.content
    if content:
        print(f"✅ DeepSeek连接成功！响应: {content}")
    else:
        print("❌ DeepSeek连接失败：响应为空")
        
except ImportError as e:
    print(f"❌ openai导入失败: {e}")
except Exception as e:
    print(f"❌ DeepSeek连接测试失败: {e}")

# 测试ccxt导入
try:
    import ccxt
    print(f"✅ ccxt导入成功，版本: {ccxt.__version__}")
except ImportError as e:
    print(f"❌ ccxt导入失败: {e}")
EOF

python3 test_deepseek_py36.py
rm -f test_deepseek_py36.py

echo "============================================================"
echo "✅ 修复完成！"
echo ""
echo "📋 接下来的步骤："
echo "1. 确保.env文件中有正确的DEEPSEEK_API_KEY"
echo "2. 重启服务器："
echo "   PORT=8081 python3 web_server.py"
echo ""
echo "🎯 预期结果："
echo "- AI模型状态显示为'已连接'"
echo "- 余额信息正常显示"
echo "- AI决策功能正常工作"
echo "============================================================"