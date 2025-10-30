#!/bin/bash
# VPS修复脚本 - 针对openai 0.10.5版本
# 解决AI功能和余额更新问题

echo "🔧 开始修复VPS环境（openai 0.10.5版本）..."

# 1. 检查Python版本
echo "============================================================"
echo "📋 检查Python版本..."
python3 --version

# 2. 升级pip
echo "============================================================"
echo "⬆️ 升级pip..."
python3 -m pip install --upgrade pip

# 3. 安装openai 0.10.5
echo "============================================================"
echo "📦 安装openai 0.10.5..."
pip3 install openai==0.10.5

# 4. 安装其他必需包
echo "============================================================"
echo "📦 安装其他必需包..."
pip3 install ccxt requests flask flask-cors schedule python-dotenv

# 5. 验证安装
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

# 6. 创建兼容的DeepSeek客户端
echo "============================================================"
echo "📝 创建兼容的DeepSeek客户端..."

cat > deepseek_client_v0105.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
兼容openai 0.10.5版本的DeepSeek客户端
"""

import os
import json
import requests
from datetime import datetime

class DeepSeekClientV0105:
    """兼容openai 0.10.5的DeepSeek客户端"""
    
    def __init__(self, api_key, base_url="https://api.deepseek.com"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def chat_completion(self, model="deepseek-chat", messages=None, max_tokens=1000, temperature=0.1, timeout=30):
        """发送聊天完成请求"""
        if messages is None:
            messages = []
        
        url = f"{self.base_url}/chat/completions"
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = requests.post(
                url, 
                headers=self.headers, 
                json=data, 
                timeout=timeout
            )
            response.raise_for_status()
            result = response.json()
            
            # 模拟openai响应格式
            class MockResponse:
                def __init__(self, data):
                    self.choices = []
                    if 'choices' in data and len(data['choices']) > 0:
                        choice_data = data['choices'][0]
                        choice = MockChoice(choice_data)
                        self.choices.append(choice)
            
            class MockChoice:
                def __init__(self, choice_data):
                    if 'message' in choice_data:
                        self.message = MockMessage(choice_data['message'])
                    else:
                        self.message = MockMessage({'content': ''})
            
            class MockMessage:
                def __init__(self, message_data):
                    self.content = message_data.get('content', '')
            
            return MockResponse(result)
            
        except Exception as e:
            raise Exception(f"DeepSeek API请求失败: {e}")

def setup_deepseek_v0105():
    """设置DeepSeek客户端"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            return None
        
        return DeepSeekClientV0105(api_key)
    except Exception:
        return None
EOF

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

# 8. 测试所有功能
echo "============================================================"
echo "🧪 测试功能..."

cat > test_all_v0105.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ 环境变量加载成功")
except ImportError:
    print("⚠️ python-dotenv未安装，跳过.env加载")

# 测试openai导入
try:
    import openai
    print(f"✅ openai导入成功，版本: {openai.__version__}")
except ImportError as e:
    print(f"❌ openai导入失败: {e}")
    sys.exit(1)

# 测试ccxt导入
try:
    import ccxt
    print(f"✅ ccxt导入成功，版本: {ccxt.__version__}")
except ImportError as e:
    print(f"❌ ccxt导入失败: {e}")

# 测试DeepSeek连接（使用自定义客户端）
try:
    from deepseek_client_v0105 import setup_deepseek_v0105
    
    client = setup_deepseek_v0105()
    if client:
        print("🔍 测试DeepSeek连接...")
        response = client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            if content:
                print(f"✅ DeepSeek连接成功！响应: {content}")
            else:
                print("❌ DeepSeek连接失败：响应为空")
        else:
            print("❌ DeepSeek连接失败：无响应")
    else:
        print("❌ DeepSeek客户端初始化失败")
        
except Exception as e:
    print(f"❌ DeepSeek连接测试失败: {e}")

print("🎯 测试完成！")
EOF

python3 test_all_v0105.py
rm -f test_all_v0105.py

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