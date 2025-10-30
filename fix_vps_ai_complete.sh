#!/bin/bash

echo "🤖 VPS AI功能完整修复脚本"
echo "============================================================"
echo "目标: 修复Python 3.6环境下的openai模块安装问题"
echo "============================================================"

# 检查Python版本
echo "🔍 检查Python环境..."
python3 --version
pip3 --version

echo ""

# 步骤1: 升级pip到最新版本
echo "📦 升级pip..."
echo "--------------------------------"
python3 -m pip install --upgrade pip
echo "✅ pip升级完成"

echo ""

# 步骤2: 卸载可能存在的旧版本openai
echo "🗑️ 清理旧版本openai..."
echo "--------------------------------"
pip3 uninstall -y openai 2>/dev/null || echo "没有发现旧版本openai"

echo ""

# 步骤3: 安装Python 3.6兼容的openai版本
echo "📥 安装Python 3.6兼容的openai..."
echo "--------------------------------"

# 尝试安装不同版本的openai，从最新兼容版本开始
OPENAI_VERSIONS=(
    "0.28.1"  # 最后一个支持Python 3.6的稳定版本
    "0.27.10"
    "0.27.8"
    "0.27.0"
)

OPENAI_INSTALLED=false

for version in "${OPENAI_VERSIONS[@]}"; do
    echo "尝试安装 openai==$version..."
    if pip3 install "openai==$version" --no-cache-dir; then
        echo "✅ openai $version 安装成功！"
        OPENAI_INSTALLED=true
        break
    else
        echo "❌ openai $version 安装失败，尝试下一个版本..."
    fi
done

if [ "$OPENAI_INSTALLED" = false ]; then
    echo "❌ 所有openai版本安装失败，尝试最基础安装..."
    pip3 install openai --no-cache-dir --force-reinstall
fi

echo ""

# 步骤4: 验证openai安装
echo "🧪 验证openai安装..."
echo "--------------------------------"

python3 << 'EOF'
try:
    import openai
    print(f"✅ openai导入成功，版本: {openai.__version__}")
    
    # 检查关键类是否可用
    if hasattr(openai, 'OpenAI'):
        print("✅ OpenAI类可用（新版本API）")
    elif hasattr(openai, 'ChatCompletion'):
        print("✅ ChatCompletion类可用（旧版本API）")
    else:
        print("⚠️ 未找到预期的API类")
        
except ImportError as e:
    print(f"❌ openai导入失败: {e}")
    exit(1)
except Exception as e:
    print(f"⚠️ openai导入有问题: {e}")
EOF

if [ $? -ne 0 ]; then
    echo "❌ openai验证失败，退出脚本"
    exit 1
fi

echo ""

# 步骤5: 安装其他必要依赖
echo "📦 安装其他必要依赖..."
echo "--------------------------------"

REQUIRED_PACKAGES=(
    "requests"
    "flask"
    "flask-cors"
    "schedule"
    "python-dotenv"
    "pandas"
)

for package in "${REQUIRED_PACKAGES[@]}"; do
    echo "安装 $package..."
    pip3 install "$package" --no-cache-dir || echo "⚠️ $package 安装可能有问题"
done

echo ""

# 步骤6: 检查.env配置
echo "⚙️ 检查环境配置..."
echo "--------------------------------"

if [ -f ".env" ]; then
    echo "✅ .env文件存在"
    
    if grep -q "DEEPSEEK_API_KEY" .env; then
        api_key=$(grep "DEEPSEEK_API_KEY" .env | cut -d'=' -f2)
        if [ "$api_key" != "your_deepseek_api_key_here" ] && [ ! -z "$api_key" ]; then
            echo "✅ DEEPSEEK_API_KEY已配置"
        else
            echo "❌ DEEPSEEK_API_KEY未正确配置"
            echo "请编辑.env文件，设置正确的API密钥"
        fi
    else
        echo "❌ .env文件中缺少DEEPSEEK_API_KEY"
        echo "请添加: DEEPSEEK_API_KEY=your_actual_api_key"
    fi
else
    echo "❌ .env文件不存在，创建模板..."
    cat > .env << 'EOF'
# DeepSeek API配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
AI_PROVIDER=deepseek

# Web服务器配置
PORT=8081
WEB_HOST=0.0.0.0

# 其他配置
DEBUG=False
EOF
    echo "✅ 已创建.env模板文件，请编辑并设置正确的API密钥"
fi

echo ""

# 步骤7: 创建AI连接测试脚本
echo "🧪 创建AI连接测试脚本..."
echo "--------------------------------"

cat > test_ai_connection.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI连接测试脚本 - Python 3.6兼容版本
"""
import os
import sys

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ 环境变量加载成功")
except ImportError:
    print("⚠️ python-dotenv未安装，手动加载.env")
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def test_openai_import():
    """测试openai导入"""
    try:
        import openai
        print(f"✅ openai导入成功，版本: {openai.__version__}")
        return openai
    except ImportError as e:
        print(f"❌ openai导入失败: {e}")
        return None

def test_deepseek_connection(openai_module):
    """测试DeepSeek连接"""
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key or api_key == 'your_deepseek_api_key_here':
        print("❌ DEEPSEEK_API_KEY未配置或无效")
        return False
    
    try:
        # 检查openai版本并使用相应的API
        openai_version = getattr(openai_module, '__version__', '0.28.1')
        print(f"🔍 使用openai版本: {openai_version}")
        
        if openai_version.startswith('0.'):
            # 旧版本API (0.x)
            print("使用旧版本API...")
            openai_module.api_key = api_key
            openai_module.api_base = "https://api.deepseek.com"
            
            response = openai_module.ChatCompletion.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": "Hello, test connection"}],
                max_tokens=10,
                temperature=0.1
            )
            content = response.choices[0].message.content
        else:
            # 新版本API (1.x)
            print("使用新版本API...")
            client = openai_module.OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com"
            )
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": "Hello, test connection"}],
                max_tokens=10,
                temperature=0.1
            )
            content = response.choices[0].message.content
        
        if content:
            print(f"✅ DeepSeek连接测试成功！响应: {content}")
            return True
        else:
            print("❌ DeepSeek连接测试失败：响应为空")
            return False
            
    except Exception as e:
        print(f"❌ DeepSeek连接测试失败: {e}")
        return False

def main():
    print("🤖 AI功能测试")
    print("=" * 50)
    
    # 测试openai导入
    openai_module = test_openai_import()
    if not openai_module:
        sys.exit(1)
    
    # 测试DeepSeek连接
    if test_deepseek_connection(openai_module):
        print("\n✅ AI功能测试通过！")
        print("现在可以启动web服务器:")
        print("PORT=8081 python3 web_server.py")
    else:
        print("\n❌ AI功能测试失败！")
        print("请检查:")
        print("1. DEEPSEEK_API_KEY是否正确")
        print("2. 网络连接是否正常")
        print("3. API余额是否充足")

if __name__ == "__main__":
    main()
EOF

chmod +x test_ai_connection.py

echo ""

# 步骤8: 运行AI连接测试
echo "🚀 运行AI连接测试..."
echo "--------------------------------"
python3 test_ai_connection.py

echo ""

# 步骤9: 提供使用说明
echo "============================================================"
echo "✅ VPS AI功能修复完成！"
echo "============================================================"
echo ""
echo "📋 修复内容:"
echo "- ✅ 安装Python 3.6兼容的openai模块"
echo "- ✅ 安装所有必要依赖包"
echo "- ✅ 检查和创建.env配置文件"
echo "- ✅ 创建AI连接测试脚本"
echo ""
echo "🚀 启动服务器:"
echo "PORT=8081 python3 web_server.py"
echo ""
echo "🧪 单独测试AI功能:"
echo "python3 test_ai_connection.py"
echo ""
echo "⚠️ 重要提醒:"
echo "1. 请确保.env文件中的DEEPSEEK_API_KEY是有效的"
echo "2. 如果仍有问题，请检查网络连接和API余额"
echo "3. 端口8081应该现在可以正常使用"
echo "============================================================"