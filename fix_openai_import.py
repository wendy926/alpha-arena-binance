#!/usr/bin/env python3
"""
修复deepseekok2.py中的openai导入问题
将openai设为可选依赖，避免因版本不兼容导致整个程序无法启动
"""

import os
import shutil

def backup_original_file():
    """备份原始文件"""
    original_file = 'deepseekok2.py'
    backup_file = 'deepseekok2.py.backup'
    
    if os.path.exists(original_file):
        shutil.copy2(original_file, backup_file)
        print(f"✅ 已备份原始文件: {backup_file}")
        return True
    else:
        print(f"❌ 原始文件不存在: {original_file}")
        return False

def fix_openai_import():
    """修复openai导入问题"""
    original_file = 'deepseekok2.py'
    
    if not os.path.exists(original_file):
        print(f"❌ 文件不存在: {original_file}")
        return False
    
    # 读取原始文件
    with open(original_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换openai导入部分
    old_import = """import os
import time
import schedule
from openai import OpenAI"""
    
    new_import = """import os
import time
import schedule

# 可选导入openai，避免版本兼容问题
try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError as e:
    print(f"警告: openai不可用，AI功能将被禁用: {e}")
    OpenAI = None
    _OPENAI_AVAILABLE = False"""
    
    # 执行替换
    if old_import in content:
        content = content.replace(old_import, new_import)
        
        # 修改AI客户端初始化部分
        old_ai_init = """# 初始化AI客户端
# 支持DeepSeek和阿里百炼Qwen
AI_PROVIDER = os.getenv('AI_PROVIDER', 'deepseek').lower()  # 'deepseek' 或 'qwen'

if AI_PROVIDER == 'qwen':
    # 阿里百炼Qwen客户端
    ai_client = OpenAI(
        api_key=os.getenv('DASHSCOPE_API_KEY'),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    AI_MODEL = "qwen-max"
    print(f"使用AI模型: 阿里百炼 {AI_MODEL}")
else:
    # DeepSeek客户端（默认）
    ai_client = OpenAI(
        api_key=os.getenv('DEEPSEEK_API_KEY'),
        base_url="https://api.deepseek.com"
    )
    AI_MODEL = "deepseek-chat"
    print(f"使用AI模型: DeepSeek {AI_MODEL}")

# 保持向后兼容
deepseek_client = ai_client"""
        
        new_ai_init = """# 初始化AI客户端
# 支持DeepSeek和阿里百炼Qwen
AI_PROVIDER = os.getenv('AI_PROVIDER', 'deepseek').lower()  # 'deepseek' 或 'qwen'

if _OPENAI_AVAILABLE and OpenAI:
    if AI_PROVIDER == 'qwen':
        # 阿里百炼Qwen客户端
        ai_client = OpenAI(
            api_key=os.getenv('DASHSCOPE_API_KEY'),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        AI_MODEL = "qwen-max"
        print(f"使用AI模型: 阿里百炼 {AI_MODEL}")
    else:
        # DeepSeek客户端（默认）
        ai_client = OpenAI(
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com"
        )
        AI_MODEL = "deepseek-chat"
        print(f"使用AI模型: DeepSeek {AI_MODEL}")
    
    # 保持向后兼容
    deepseek_client = ai_client
else:
    print("⚠️ OpenAI不可用，AI功能将被禁用")
    ai_client = None
    deepseek_client = None
    AI_MODEL = "disabled"
    AI_PROVIDER = "none"
    
    # 创建一个模拟的AI客户端
    class MockAIClient:
        def __init__(self):
            pass
        
        def chat_completions_create(self, *args, **kwargs):
            return type('MockResponse', (), {
                'choices': [type('MockChoice', (), {
                    'message': type('MockMessage', (), {
                        'content': '{"signal": "HOLD", "confidence": "LOW", "reason": "AI功能未启用"}'
                    })()
                })()]
            })()
    
    ai_client = MockAIClient()
    deepseek_client = ai_client"""
        
        if old_ai_init in content:
            content = content.replace(old_ai_init, new_ai_init)
        
        # 写入修改后的文件
        with open(original_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 已修复openai导入问题")
        return True
    else:
        print("⚠️ 未找到需要替换的导入代码，可能已经修复过了")
        return True

def main():
    print("🔧 修复deepseekok2.py中的openai导入问题")
    print("=" * 40)
    
    # 备份原始文件
    if backup_original_file():
        # 修复导入问题
        if fix_openai_import():
            print("\n✅ 修复完成！")
            print("\n现在可以尝试启动web服务器:")
            print("python3 web_server.py")
        else:
            print("\n❌ 修复失败")
    else:
        print("\n❌ 无法备份原始文件，修复中止")

if __name__ == "__main__":
    main()