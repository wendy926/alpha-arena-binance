#!/bin/bash

# DeepSeek连接修复脚本
# Fix DeepSeek Connection Script

echo "🤖 修复DeepSeek连接问题..."
echo "================================"

# 步骤1: 安装openai包
echo "📦 安装openai包..."
pip3 install openai==1.3.0 --no-deps --force-reinstall 2>/dev/null || \
pip3 install openai==0.28.1 --no-deps --force-reinstall 2>/dev/null || \
pip3 install openai --no-deps --force-reinstall

# 检查安装结果
python3 -c "import openai; print('✅ openai包安装成功')" 2>/dev/null || {
    echo "❌ openai包安装失败，尝试备用方法..."
    
    # 备用安装方法
    python3 -m pip install --user openai==0.28.1 --no-deps 2>/dev/null || \
    python3 -m pip install --user openai --no-deps
}

echo ""

# 步骤2: 检查环境变量
echo "🔑 检查DeepSeek API配置..."

if [ -f ".env" ]; then
    echo "发现.env文件"
    if grep -q "DEEPSEEK_API_KEY" .env; then
        echo "✅ 找到DEEPSEEK_API_KEY配置"
    else
        echo "⚠️ 未找到DEEPSEEK_API_KEY，添加配置..."
        echo "" >> .env
        echo "# DeepSeek API配置" >> .env
        echo "DEEPSEEK_API_KEY=your_deepseek_api_key_here" >> .env
        echo "AI_PROVIDER=deepseek" >> .env
    fi
    
    if grep -q "AI_PROVIDER" .env; then
        echo "✅ 找到AI_PROVIDER配置"
    else
        echo "⚠️ 未找到AI_PROVIDER，添加配置..."
        echo "AI_PROVIDER=deepseek" >> .env
    fi
else
    echo "⚠️ 未找到.env文件，创建配置..."
    cat > .env << EOF
# DeepSeek API配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
AI_PROVIDER=deepseek

# 其他配置
PORT=8080
EOF
fi

echo ""

# 步骤3: 修复deepseekok2.py中的openai导入
echo "🔧 修复AI模块导入..."

# 备份原文件
cp deepseekok2.py deepseekok2.py.backup.$(date +%s)

# 检查并修复openai导入
python3 << 'EOF'
import re

# 读取文件
with open('deepseekok2.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 检查是否已经有try-except包装
if '_OPENAI_AVAILABLE' not in content:
    print("添加openai导入保护...")
    
    # 找到openai导入行
    openai_import_pattern = r'^(import openai)$'
    
    if re.search(openai_import_pattern, content, re.MULTILINE):
        # 替换openai导入
        new_import = '''# OpenAI导入保护
try:
    import openai
    _OPENAI_AVAILABLE = True
    print("✅ OpenAI模块加载成功")
except ImportError as e:
    print(f"⚠️ OpenAI模块不可用: {e}")
    _OPENAI_AVAILABLE = False
    # 创建mock openai对象
    class MockOpenAI:
        def __init__(self, *args, **kwargs):
            pass
    openai = None'''
        
        content = re.sub(openai_import_pattern, new_import, content, flags=re.MULTILINE)
        
        # 写回文件
        with open('deepseekok2.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ OpenAI导入保护已添加")
    else:
        print("✅ OpenAI导入已存在保护")
else:
    print("✅ OpenAI导入保护已存在")
EOF

echo ""

# 步骤4: 测试DeepSeek连接
echo "🧪 测试DeepSeek连接..."

python3 << 'EOF'
import os
import sys

# 加载环境变量
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

try:
    import openai
    
    # 检查API密钥
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key or api_key == 'your_deepseek_api_key_here':
        print("❌ 请设置有效的DEEPSEEK_API_KEY")
        print("编辑.env文件，设置: DEEPSEEK_API_KEY=sk-your-actual-key")
        sys.exit(1)
    
    # 测试连接
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )
    
    # 发送测试请求
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "测试连接"}],
        max_tokens=10
    )
    
    print("✅ DeepSeek连接测试成功！")
    print(f"响应: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"❌ DeepSeek连接测试失败: {e}")
    print("请检查:")
    print("1. DEEPSEEK_API_KEY是否正确")
    print("2. 网络连接是否正常")
    print("3. API余额是否充足")
EOF

echo ""

# 步骤5: 提供启动指令
echo "🚀 修复完成！"
echo "================================"
echo ""
echo "下一步操作:"
echo "1. 编辑.env文件，设置你的DeepSeek API密钥:"
echo "   DEEPSEEK_API_KEY=sk-your-actual-deepseek-key"
echo ""
echo "2. 启动服务器:"
echo "   python3 web_server.py"
echo ""
echo "3. 或使用备用端口:"
echo "   PORT=8081 python3 web_server.py"
echo ""
echo "4. 访问地址:"
echo "   http://你的VPS_IP:8080"
echo "   http://你的VPS_IP:8081"
echo ""
echo "💡 如果仍有问题，请检查:"
echo "- DeepSeek API密钥是否有效"
echo "- VPS网络是否能访问api.deepseek.com"
echo "- API余额是否充足"