#!/bin/bash

echo "🔍 检查VPS数据库状态和交易数据..."
echo "=================================="

# 检查容器状态
echo "📊 检查容器状态："
docker-compose ps

echo ""
echo "🔗 检查数据库连接："
docker-compose exec mysql mysql -u trader -ptrader123 -e "SELECT 'Database connection OK' as status;" trading_bot

echo ""
echo "📋 检查数据库表结构："
docker-compose exec mysql mysql -u trader -ptrader123 -e "SHOW TABLES;" trading_bot

echo ""
echo "📈 检查交易记录数量："
docker-compose exec mysql mysql -u trader -ptrader123 -e "SELECT COUNT(*) as total_trades FROM trades;" trading_bot 2>/dev/null || echo "❌ trades表不存在或无法访问"

echo ""
echo "💰 检查持仓记录数量："
docker-compose exec mysql mysql -u trader -ptrader123 -e "SELECT COUNT(*) as total_positions FROM positions;" trading_bot 2>/dev/null || echo "❌ positions表不存在或无法访问"

echo ""
echo "📊 检查最近的交易记录："
docker-compose exec mysql mysql -u trader -ptrader123 -e "SELECT * FROM trades ORDER BY timestamp DESC LIMIT 5;" trading_bot 2>/dev/null || echo "❌ 无法查询trades表"

echo ""
echo "🎯 检查当前持仓："
docker-compose exec mysql mysql -u trader -ptrader123 -e "SELECT * FROM positions WHERE is_active = 1;" trading_bot 2>/dev/null || echo "❌ 无法查询positions表"

echo ""
echo "📱 检查应用日志中的数据库连接："
docker logs btc-trading-bot --tail 30 | grep -i "database\|mysql\|connection\|error"

echo ""
echo "🌐 测试网站API响应："
curl -s http://localhost:8080/api/trades | head -200

echo ""
echo "🔧 检查数据卷状态："
docker volume ls | grep mysql

echo ""
echo "📁 检查MySQL数据目录："
docker-compose exec mysql ls -la /var/lib/mysql/trading_bot/ 2>/dev/null || echo "❌ 无法访问MySQL数据目录"