#!/bin/bash

echo "🔧 修复OpenAI模块兼容性问题"
echo "============================="

echo "检测到pandas版本兼容性问题..."
echo "当前系统pandas版本过低，无法满足openai>=1.0的要求"
echo ""

echo "解决方案1: 安装兼容的openai版本..."
# 尝试安装较老但兼容的openai版本
pip3 install "openai<1.0" --no-deps

if [ $? -eq 0 ]; then
    echo "✅ 安装兼容版本的openai成功"
else
    echo "方案1失败，尝试方案2..."
    
    echo "解决方案2: 升级pandas并安装openai..."
    # 尝试升级pandas
    pip3 install --upgrade pandas
    
    if [ $? -eq 0 ]; then
        echo "✅ pandas升级成功，现在安装openai..."
        pip3 install openai
    else
        echo "方案2失败，尝试方案3..."
        
        echo "解决方案3: 使用--force-reinstall强制安装..."
        pip3 install openai --force-reinstall --no-deps
        
        if [ $? -eq 0 ]; then
            echo "✅ 强制安装成功"
        else
            echo "❌ 所有方案都失败了"
            echo ""
            echo "手动解决方案:"
            echo "1. 升级Python到3.8+: yum update python3"
            echo "2. 或者修改代码以移除openai依赖"
            exit 1
        fi
    fi
fi

echo ""
echo "🔍 验证安装..."
python3 -c "
try:
    import openai
    print('✅ openai模块可用')
    print('版本:', openai.__version__ if hasattr(openai, '__version__') else '未知')
except ImportError as e:
    print('❌ openai模块仍不可用:', e)
except Exception as e:
    print('⚠️ openai模块导入有问题:', e)
"

echo ""
echo "现在可以尝试启动web服务器:"
echo "python3 web_server.py"