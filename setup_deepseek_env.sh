#!/bin/bash

# DeepSeek环境配置脚本
# Setup DeepSeek Environment Script

echo "🔧 配置DeepSeek环境..."
echo "================================"

# 检查是否存在.env文件
if [ -f ".env" ]; then
    echo "发现现有.env文件，创建备份..."
    cp .env .env.backup.$(date +%s)
fi

# 创建新的.env文件
echo "📝 创建DeepSeek配置文件..."

cat > .env << 'EOF'
# ========================================
# BTC自动交易机器人配置文件 - DeepSeek版本
# ========================================

# ========== AI模型配置 ==========
AI_PROVIDER=deepseek

# DeepSeek API密钥 - 请替换为你的真实密钥
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here

# ========== 服务器配置 ==========
PORT=8080

# ========== 交易模式 ==========
# 仅纸面交易（不执行真实下单）
PAPER_TRADING=true

# ========== 数据库配置 ==========
# 使用SQLite作为默认数据库
DB_TYPE=sqlite

# ========== OKX交易所配置（可选，纸面交易时不需要真实密钥） ==========
OKX_API_KEY=demo-api-key
OKX_SECRET=demo-secret
OKX_PASSWORD=demo-password
EOF

echo "✅ .env文件已创建"
echo ""

# 显示配置指南
echo "🔑 重要：请设置你的DeepSeek API密钥"
echo "================================"
echo ""
echo "1. 获取DeepSeek API密钥:"
echo "   - 访问: https://platform.deepseek.com/"
echo "   - 注册/登录账户"
echo "   - 创建API密钥"
echo ""
echo "2. 编辑.env文件，替换API密钥:"
echo "   nano .env"
echo "   或"
echo "   vi .env"
echo ""
echo "   将 'sk-your-deepseek-api-key-here' 替换为你的真实密钥"
echo ""
echo "3. 示例配置:"
echo "   DEEPSEEK_API_KEY=sk-1234567890abcdef..."
echo ""

# 检查当前配置
echo "📋 当前配置预览:"
echo "--------------------------------"
cat .env | grep -E "^(AI_PROVIDER|DEEPSEEK_API_KEY|PORT|PAPER_TRADING|DB_TYPE)="
echo "--------------------------------"
echo ""

echo "💡 配置完成后，运行以下命令启动服务:"
echo "   ./fix_deepseek_connection.sh"
echo "   python3 web_server.py"