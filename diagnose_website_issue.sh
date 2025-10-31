#!/bin/bash

echo "🔍 诊断网站问题"
echo "=================================="
echo ""

# 1. 检查应用日志
echo "📋 1. 检查应用日志..."
ssh root@47.236.115.4 "cd /root/alpha-arena-binance && docker-compose logs --tail=50 btc-trading-bot | grep -E '(error|Error|ERROR|DeepSeek|deepseek|API|api|encoding|utf|中文)'"

echo ""
echo "📋 2. 检查环境变量配置..."
ssh root@47.236.115.4 "cd /root/alpha-arena-binance && cat .env | grep -E '(DEEPSEEK|API|MYSQL|DB)'"

echo ""
echo "📋 3. 测试API端点响应..."
echo "    🔗 测试 /api/dashboard..."
ssh root@47.236.115.4 "curl -s http://localhost:8080/api/dashboard | python3 -m json.tool"

echo ""
echo "    🔗 测试 /api/trades..."
ssh root@47.236.115.4 "curl -s http://localhost:8080/api/trades | python3 -m json.tool"

echo ""
echo "📋 4. 检查数据库中的中文数据..."
ssh root@47.236.115.4 "mysql -u trader -ptrader123 -h localhost trading_bot -e \"SELECT reason FROM trades LIMIT 5;\""

echo ""
echo "📋 5. 检查容器状态..."
ssh root@47.236.115.4 "cd /root/alpha-arena-binance && docker-compose ps"

echo ""
echo "✅ 诊断完成！"