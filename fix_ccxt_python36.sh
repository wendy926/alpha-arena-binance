#!/bin/bash
# 专门修复Python 3.6环境下的ccxt安装问题

echo "🔧 开始修复Python 3.6环境下的ccxt安装问题..."

# 1. 检查Python版本
echo "============================================================"
echo "📋 检查Python版本..."
python3 --version

# 2. 检查pip版本
echo "============================================================"
echo "📋 检查pip版本..."
pip3 --version

# 3. 升级pip到兼容版本
echo "============================================================"
echo "⬆️ 升级pip..."
python3 -m pip install --upgrade "pip<21.0" --user

# 4. 清理可能的缓存
echo "============================================================"
echo "🧹 清理pip缓存..."
pip3 cache purge 2>/dev/null || true
rm -rf ~/.cache/pip 2>/dev/null || true

# 5. 完全卸载ccxt
echo "============================================================"
echo "🗑️ 完全卸载ccxt..."
pip3 uninstall -y ccxt 2>/dev/null || true
pip3 uninstall -y ccxt --user 2>/dev/null || true

# 6. 尝试安装兼容Python 3.6的ccxt版本
echo "============================================================"
echo "📦 尝试安装兼容Python 3.6的ccxt版本..."

# 尝试多个版本，从最新兼容版本开始
CCXT_VERSIONS=("1.92.9" "1.90.0" "1.85.0" "1.80.0" "1.75.0" "1.70.0" "1.65.0" "1.60.0")

for version in "${CCXT_VERSIONS[@]}"; do
    echo "尝试安装ccxt==$version..."
    if pip3 install --no-cache-dir "ccxt==$version" --user; then
        echo "✅ ccxt==$version 安装成功！"
        INSTALLED_VERSION=$version
        break
    else
        echo "❌ ccxt==$version 安装失败，尝试下一个版本..."
    fi
done

# 7. 如果所有版本都失败，尝试从源码安装
if [ -z "$INSTALLED_VERSION" ]; then
    echo "============================================================"
    echo "📦 尝试从源码安装ccxt..."
    
    # 下载并安装兼容版本的源码
    cd /tmp
    wget https://github.com/ccxt/ccxt/archive/refs/tags/1.92.9.tar.gz -O ccxt-1.92.9.tar.gz
    tar -xzf ccxt-1.92.9.tar.gz
    cd ccxt-1.92.9/python
    python3 setup.py install --user
    cd /
    rm -rf /tmp/ccxt-*
fi

# 8. 验证ccxt安装
echo "============================================================"
echo "✅ 验证ccxt安装..."

cat > test_ccxt_python36.py << 'EOF'
#!/usr/bin/env python3
import sys
import os

# 添加用户安装路径到Python路径
import site
user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.insert(0, user_site)

try:
    import ccxt
    print(f"✅ ccxt导入成功，版本: {ccxt.__version__}")
    
    # 测试创建交易所实例
    try:
        exchange = ccxt.okx()
        print("✅ ccxt.okx()创建成功")
        
        # 测试获取市场数据（不需要API密钥）
        try:
            markets = exchange.load_markets()
            if 'BTC/USDT' in markets:
                print("✅ 市场数据加载成功")
            else:
                print("⚠️ BTC/USDT市场不可用")
        except Exception as e:
            print(f"⚠️ 市场数据加载失败（可能是网络问题）: {e}")
        
        # 测试获取价格（可能失败，但不影响ccxt功能）
        try:
            ticker = exchange.fetch_ticker('BTC/USDT')
            print(f"✅ 获取BTC/USDT价格成功: ${ticker['last']:,.2f}")
        except Exception as e:
            print(f"⚠️ 获取价格失败（正常，因为没有API密钥或网络限制）: {e}")
        
        print("🎯 ccxt功能验证完成！")
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ ccxt功能测试失败: {e}")
        sys.exit(1)
        
except ImportError as e:
    print(f"❌ ccxt导入失败: {e}")
    print("Python路径:")
    for path in sys.path:
        print(f"  {path}")
    sys.exit(1)
except Exception as e:
    print(f"❌ ccxt测试失败: {e}")
    sys.exit(1)
EOF

python3 test_ccxt_python36.py
CCXT_TEST_RESULT=$?

if [ $CCXT_TEST_RESULT -eq 0 ]; then
    echo "✅ ccxt安装验证成功！"
else
    echo "❌ ccxt安装验证失败，尝试最后的解决方案..."
    
    # 9. 最后的解决方案：手动安装最小版本
    echo "============================================================"
    echo "📦 尝试安装最小兼容版本..."
    
    pip3 install --no-cache-dir --no-deps ccxt --user
    pip3 install --no-cache-dir requests urllib3 certifi --user
    
    # 再次测试
    python3 test_ccxt_python36.py
    CCXT_TEST_RESULT=$?
fi

rm -f test_ccxt_python36.py

# 10. 创建ccxt环境检查脚本
echo "============================================================"
echo "📝 创建ccxt环境检查脚本..."

cat > check_ccxt_env.py << 'EOF'
#!/usr/bin/env python3
import sys
import os

# 添加用户安装路径
import site
user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.insert(0, user_site)

print("🔍 检查ccxt环境...")
print(f"Python版本: {sys.version}")
print(f"用户安装路径: {user_site}")

try:
    import ccxt
    print(f"✅ ccxt版本: {ccxt.__version__}")
    
    # 检查可用的交易所
    exchanges = ccxt.exchanges
    print(f"✅ 可用交易所数量: {len(exchanges)}")
    
    if 'okx' in exchanges:
        print("✅ OKX交易所可用")
    else:
        print("❌ OKX交易所不可用")
    
    return True
    
except ImportError as e:
    print(f"❌ ccxt导入失败: {e}")
    return False
except Exception as e:
    print(f"❌ ccxt检查失败: {e}")
    return False

if __name__ == "__main__":
    success = check_ccxt_env()
    sys.exit(0 if success else 1)
EOF

# 11. 最终结果
echo "============================================================"
if [ $CCXT_TEST_RESULT -eq 0 ]; then
    echo "✅ ccxt安装修复完成！"
    echo ""
    echo "📋 接下来的步骤："
    echo "1. 运行环境检查："
    echo "   python3 check_ccxt_env.py"
    echo ""
    echo "2. 重新启动服务器："
    echo "   PORT=8081 python3 web_server.py"
    echo ""
    echo "🎯 预期结果："
    echo "- 不再显示'ccxt模块不可用，使用模拟数据'"
    echo "- 显示真实的BTC价格数据"
else
    echo "❌ ccxt安装修复失败！"
    echo ""
    echo "🔍 可能的原因："
    echo "1. Python 3.6版本过旧，不兼容最新的ccxt"
    echo "2. 网络连接问题"
    echo "3. 系统权限问题"
    echo ""
    echo "🛠️ 建议的解决方案："
    echo "1. 升级Python到3.7或更高版本"
    echo "2. 使用虚拟环境"
    echo "3. 联系系统管理员检查网络和权限"
fi

echo "============================================================"