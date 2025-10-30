#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速AI功能测试脚本
用于验证VPS环境下的AI功能是否正常工作
"""
import os
import sys

def load_env():
    """加载环境变量"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ 使用python-dotenv加载环境变量")
    except ImportError:
        print("⚠️ python-dotenv未安装，手动加载.env")
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
            print("✅ 手动加载.env文件成功")
        else:
            print("❌ .env文件不存在")

def test_openai():
    """测试openai模块"""
    try:
        import openai
        print(f"✅ openai模块导入成功，版本: {openai.__version__}")
        return openai
    except ImportError as e:
        print(f"❌ openai模块导入失败: {e}")
        print("请运行: pip3 install 'openai==0.28.1'")
        return None

def test_deepseek_api(openai_module):
    """测试DeepSeek API连接"""
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("❌ DEEPSEEK_API_KEY未设置")
        return False
    
    if api_key == 'your_deepseek_api_key_here':
        print("❌ DEEPSEEK_API_KEY未正确配置")
        return False
    
    print(f"🔑 使用API密钥: {api_key[:10]}...")
    
    try:
        # 检查openai版本
        version = getattr(openai_module, '__version__', '0.28.1')
        print(f"🔍 openai版本: {version}")
        
        if version.startswith('0.'):
            # 旧版本API
            print("使用旧版本API...")
            openai_module.api_key = api_key
            openai_module.api_base = "https://api.deepseek.com"
            
            response = openai_module.ChatCompletion.create(
                model="deepseek-chat",
                messages=[
                    {"role": "user", "content": "请回复'AI连接测试成功'"}
                ],
                max_tokens=20,
                temperature=0.1
            )
            content = response.choices[0].message.content.strip()
        else:
            # 新版本API
            print("使用新版本API...")
            client = openai_module.OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com"
            )
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "user", "content": "请回复'AI连接测试成功'"}
                ],
                max_tokens=20,
                temperature=0.1
            )
            content = response.choices[0].message.content.strip()
        
        print(f"✅ DeepSeek API测试成功！")
        print(f"📝 AI响应: {content}")
        return True
        
    except Exception as e:
        print(f"❌ DeepSeek API测试失败: {e}")
        print("可能的原因:")
        print("1. API密钥无效")
        print("2. 网络连接问题")
        print("3. API余额不足")
        print("4. 请求频率过高")
        return False

def test_deepseekok2_import():
    """测试deepseekok2模块导入"""
    try:
        import deepseekok2
        print("✅ deepseekok2模块导入成功")
        
        # 检查AI相关变量
        if hasattr(deepseekok2, '_OPENAI_AVAILABLE'):
            print(f"🔍 _OPENAI_AVAILABLE: {deepseekok2._OPENAI_AVAILABLE}")
        
        if hasattr(deepseekok2, 'ai_client'):
            if deepseekok2.ai_client is not None:
                print("✅ ai_client已初始化")
            else:
                print("❌ ai_client为None")
        
        if hasattr(deepseekok2, 'AI_MODEL'):
            print(f"🤖 AI_MODEL: {deepseekok2.AI_MODEL}")
        
        return True
    except ImportError as e:
        print(f"❌ deepseekok2模块导入失败: {e}")
        return False

def main():
    print("🤖 快速AI功能测试")
    print("=" * 50)
    
    # 1. 加载环境变量
    load_env()
    print()
    
    # 2. 测试openai模块
    openai_module = test_openai()
    if not openai_module:
        print("\n❌ 测试失败：openai模块不可用")
        print("解决方案：运行 fix_vps_ai_complete.sh 脚本")
        sys.exit(1)
    print()
    
    # 3. 测试DeepSeek API
    api_success = test_deepseek_api(openai_module)
    print()
    
    # 4. 测试deepseekok2模块
    module_success = test_deepseekok2_import()
    print()
    
    # 5. 总结
    print("=" * 50)
    if api_success and module_success:
        print("✅ AI功能测试全部通过！")
        print("🚀 现在可以启动web服务器:")
        print("   PORT=8081 python3 web_server.py")
    else:
        print("❌ AI功能测试失败！")
        print("🔧 请运行修复脚本:")
        print("   chmod +x fix_vps_ai_complete.sh")
        print("   ./fix_vps_ai_complete.sh")

if __name__ == "__main__":
    main()