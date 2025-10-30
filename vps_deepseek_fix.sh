#!/bin/bash

# VPS DeepSeek连接修复脚本
# 直接在VPS上执行此脚本来修复DeepSeek连接问题

echo "🚀 VPS DeepSeek连接修复开始..."
echo "================================"

# 检查当前目录
echo "📍 当前目录: $(pwd)"
if [ ! -f "deepseekok2.py" ]; then
    echo "❌ 未找到deepseekok2.py，请确保在正确的项目目录中"
    echo "尝试切换到项目目录..."
    cd /root/alpha-arena 2>/dev/null || cd ~/alpha-arena 2>/dev/null || {
        echo "❌ 无法找到项目目录，请手动切换到包含deepseekok2.py的目录"
        exit 1
    }
fi

echo "✅ 项目目录确认: $(pwd)"
echo ""

# 步骤1: 强制安装openai包
echo "📦 安装openai包..."
echo "--------------------------------"

# 尝试多种安装方法
pip3 install openai==1.3.0 --force-reinstall --no-cache-dir 2>/dev/null && echo "✅ openai 1.3.0 安装成功" || {
    echo "⚠️ openai 1.3.0 安装失败，尝试其他版本..."
    pip3 install openai==0.28.1 --force-reinstall --no-cache-dir 2>/dev/null && echo "✅ openai 0.28.1 安装成功" || {
        echo "⚠️ 标准安装失败，尝试用户安装..."
        pip3 install --user openai --force-reinstall --no-cache-dir 2>/dev/null && echo "✅ openai 用户安装成功" || {
            echo "❌ 所有openai安装方法都失败了"
        }
    }
}

# 验证安装
python3 -c "import openai; print('✅ openai模块验证成功')" 2>/dev/null || {
    echo "❌ openai模块验证失败，但继续执行..."
}

echo ""

# 步骤2: 创建/更新.env配置文件
echo "🔧 配置环境变量..."
echo "--------------------------------"

# 备份现有.env文件
if [ -f ".env" ]; then
    cp .env .env.backup.$(date +%s)
    echo "✅ 已备份现有.env文件"
fi

# 创建新的.env配置
cat > .env << 'EOF'
# ========================================
# BTC自动交易机器人配置文件 - VPS版本
# ========================================

# ========== AI模型配置 ==========
AI_PROVIDER=deepseek

# DeepSeek API密钥 - 请替换为真实密钥
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here

# ========== 服务器配置 ==========
PORT=8080

# ========== 交易模式 ==========
# 仅纸面交易（不执行真实下单）
PAPER_TRADING=true

# ========== 数据库配置 ==========
# 使用SQLite作为默认数据库
DB_TYPE=sqlite

# ========== OKX交易所配置（演示用） ==========
OKX_API_KEY=demo-api-key
OKX_SECRET=demo-secret
OKX_PASSWORD=demo-password
EOF

echo "✅ .env配置文件已创建"
echo ""

# 步骤3: 测试Python环境
echo "🐍 测试Python环境..."
echo "--------------------------------"

python3 << 'EOF'
import sys
print(f"Python版本: {sys.version}")

# 测试openai导入
try:
    import openai
    print("✅ openai模块可用")
    
    # 测试OpenAI类
    try:
        from openai import OpenAI
        print("✅ OpenAI类可用 (新版本)")
    except ImportError:
        print("⚠️ OpenAI类不可用，可能是旧版本")
        
except ImportError as e:
    print(f"❌ openai模块不可用: {e}")

# 测试其他依赖
modules = ['pandas', 'requests', 'schedule', 'flask', 'flask_cors']
for module in modules:
    try:
        __import__(module)
        print(f"✅ {module} 可用")
    except ImportError:
        print(f"❌ {module} 不可用")
EOF

echo ""

# 步骤4: 修复deepseekok2.py中的openai导入
echo "🔧 修复deepseekok2.py..."
echo "--------------------------------"

# 检查文件是否存在
if [ ! -f "deepseekok2.py" ]; then
    echo "❌ deepseekok2.py文件不存在"
    exit 1
fi

# 备份原文件
cp deepseekok2.py deepseekok2.py.backup.$(date +%s)
echo "✅ 已备份deepseekok2.py"

# 检查是否已经有保护性导入
if grep -q "_OPENAI_AVAILABLE" deepseekok2.py; then
    echo "✅ deepseekok2.py已有openai导入保护"
else
    echo "⚠️ 添加openai导入保护..."
    
    # 使用Python脚本修复导入
    python3 << 'EOF'
import re

# 读取文件
with open('deepseekok2.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 检查并修复导入
if 'from openai import OpenAI' in content and '_OPENAI_AVAILABLE' not in content:
    # 替换导入部分
    old_pattern = r'from openai import OpenAI'
    new_import = '''# 可选导入openai，避免版本兼容问题
try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError as e:
    print(f"警告: openai不可用，AI功能将被禁用: {e}")
    OpenAI = None
    _OPENAI_AVAILABLE = False'''
    
    content = re.sub(old_pattern, new_import, content)
    
    # 写回文件
    with open('deepseekok2.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 已添加openai导入保护")
else:
    print("✅ 文件已有保护或无需修改")
EOF
fi

echo ""

# 步骤5: 测试DeepSeek连接
echo "🧪 测试DeepSeek连接..."
echo "--------------------------------"

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

# 检查API密钥
api_key = os.getenv('DEEPSEEK_API_KEY')
if not api_key or api_key == 'sk-your-deepseek-api-key-here':
    print("❌ 请设置有效的DEEPSEEK_API_KEY")
    print("编辑.env文件: nano .env")
    print("设置: DEEPSEEK_API_KEY=sk-your-actual-key")
    sys.exit(0)

try:
    import openai
    from openai import OpenAI
    
    # 测试连接
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )
    
    print("🔍 发送测试请求...")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=10
    )
    
    print("✅ DeepSeek连接测试成功！")
    print(f"响应: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"❌ DeepSeek连接测试失败: {e}")
    print("可能的原因:")
    print("1. API密钥无效")
    print("2. 网络连接问题")
    print("3. API余额不足")
EOF

echo ""

# 步骤6: 检查端口占用并启动服务
echo "🚀 准备启动服务..."
echo "--------------------------------"

# 检查端口8080
if netstat -tuln 2>/dev/null | grep -q ":8080 "; then
    echo "⚠️ 端口8080被占用，尝试清理..."
    
    # 尝试找到并终止占用进程
    PID=$(netstat -tuln 2>/dev/null | grep ":8080 " | awk '{print $7}' | cut -d'/' -f1 | head -1)
    if [ -n "$PID" ] && [ "$PID" != "-" ]; then
        echo "终止进程 $PID..."
        kill -9 "$PID" 2>/dev/null
        sleep 2
    fi
    
    # 使用备用端口
    echo "使用备用端口8081..."
    export PORT=8081
else
    echo "✅ 端口8080可用"
fi

echo ""
echo "🎉 修复完成！"
echo "================================"
echo ""
echo "下一步操作:"
echo "1. 设置DeepSeek API密钥:"
echo "   nano .env"
echo "   将 DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here"
echo "   改为 DEEPSEEK_API_KEY=sk-你的真实密钥"
echo ""
echo "2. 启动服务器:"
echo "   python3 web_server.py"
echo ""
echo "3. 或使用备用端口:"
echo "   PORT=8081 python3 web_server.py"
echo ""
echo "4. 访问地址:"
echo "   http://47.79.95.72:8080"
echo "   http://47.79.95.72:8081"
echo ""
echo "💡 如果仍有问题:"
echo "- 检查防火墙设置"
echo "- 确认DeepSeek API密钥有效"
echo "- 查看服务器日志"