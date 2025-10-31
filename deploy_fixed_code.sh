#!/bin/bash

echo "🚀 部署修复后的代码"
echo "=================================="
echo "📋 修复内容："
echo "    - 所有SQL查询中的signal字段都使用反引号"
echo "    - 包括SELECT、INSERT和CREATE TABLE语句"
echo ""

# 1. 上传修复后的paper_trading.py文件
echo "📤 1. 上传修复后的paper_trading.py文件..."
scp paper_trading.py root@47.236.115.4:/root/alpha-arena-binance/

# 2. 重启应用容器
echo "🔄 2. 重启应用容器..."
ssh root@47.236.115.4 "cd /root/alpha-arena-binance && docker-compose restart btc-trading-bot"

# 等待容器启动
echo "⏳ 等待容器启动..."
sleep 15

# 3. 测试API端点
echo "🧪 3. 测试修复结果..."
echo "    📊 测试trades API..."
TRADES_RESPONSE=$(ssh root@47.236.115.4 "curl -s http://localhost:5000/api/trades")
echo "    Trades API返回: $TRADES_RESPONSE"

echo "    📊 测试dashboard API..."
DASHBOARD_RESPONSE=$(ssh root@47.236.115.4 "curl -s http://localhost:5000/api/dashboard")
echo "    Dashboard API返回: $DASHBOARD_RESPONSE"

# 4. 检查应用日志
echo "    🔍 检查应用日志..."
ssh root@47.236.115.4 "cd /root/alpha-arena-binance && docker-compose logs --tail=20 btc-trading-bot | grep -E '(error|Error|ERROR|SQL|sql|1064)'"

echo ""
echo "✅ 代码部署完成！"
echo "📊 如果trades API返回了数据，说明修复成功"
echo "❌ 如果仍然返回空数组，请检查日志中的错误信息"