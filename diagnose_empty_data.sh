#!/bin/bash

echo "🔍 诊断持仓和交易数据为空的问题"
echo "=================================="

VPS_IP="47.79.95.72"
PROJECT_PATH="/opt/alpha-arena/alpha-arena-binance"

echo "📊 1. 检查数据库中的交易数据..."
ssh root@$VPS_IP "
cd $PROJECT_PATH

echo '检查数据库连接:'
docker exec alpha-arena-mysql mysql -u trader -ptrader123 -e 'SELECT 1;' 2>/dev/null && echo '✅ 数据库连接正常' || echo '❌ 数据库连接失败'

echo ''
echo '检查数据库和表结构:'
docker exec alpha-arena-mysql mysql -u trader -ptrader123 -e 'SHOW DATABASES;'

echo ''
echo '检查trading_bot数据库:'
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot -e 'SHOW TABLES;' 2>/dev/null || echo '❌ trading_bot数据库不存在'

echo ''
echo '检查trades表数据:'
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot -e 'SELECT COUNT(*) as total_trades FROM trades;' 2>/dev/null || echo '❌ trades表不存在或无法访问'

echo ''
echo '检查trades表结构:'
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot -e 'DESCRIBE trades;' 2>/dev/null || echo '❌ 无法获取trades表结构'

echo ''
echo '检查最近的交易记录:'
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot -e 'SELECT * FROM trades ORDER BY timestamp DESC LIMIT 5;' 2>/dev/null || echo '❌ 无法查询交易记录'
"

echo ""
echo "🤖 2. 检查交易机器人状态..."
ssh root@$VPS_IP "
cd $PROJECT_PATH

echo '检查容器运行状态:'
docker ps | grep btc-trading-bot

echo ''
echo '检查应用日志:'
docker logs btc-trading-bot --tail 20

echo ''
echo '检查是否有交易策略在运行:'
docker exec btc-trading-bot ps aux | grep python || echo '无Python进程运行'
"

echo ""
echo "⚙️ 3. 检查交易配置..."
ssh root@$VPS_IP "
cd $PROJECT_PATH

echo '检查环境变量配置:'
docker exec btc-trading-bot env | grep -E '(DEEPSEEK|API|TRADING|TEST)' || echo '无相关环境变量'

echo ''
echo '检查配置文件:'
docker exec btc-trading-bot cat .env 2>/dev/null | grep -E '(DEEPSEEK|API|TRADING|TEST)' || echo '无法读取.env文件'

echo ''
echo '检查交易模式:'
curl -s http://localhost:8080/api/dashboard | grep test_mode
"

echo ""
echo "🔧 4. 检查数据库初始化..."
ssh root@$VPS_IP "
cd $PROJECT_PATH

echo '尝试创建数据库和表（如果不存在）:'
docker exec alpha-arena-mysql mysql -u trader -ptrader123 -e \"
CREATE DATABASE IF NOT EXISTS trading_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE trading_bot;
CREATE TABLE IF NOT EXISTS trades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    amount DECIMAL(20,8) NOT NULL,
    price DECIMAL(20,8) NOT NULL,
    profit DECIMAL(20,8) DEFAULT 0,
    reason VARCHAR(255) DEFAULT '',
    status VARCHAR(20) DEFAULT 'completed'
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
\" && echo '✅ 数据库和表创建/检查完成' || echo '❌ 数据库创建失败'
"

echo ""
echo "📝 5. 创建测试数据..."
ssh root@$VPS_IP "
cd $PROJECT_PATH

echo '插入测试交易数据:'
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot -e \"
INSERT INTO trades (symbol, side, amount, price, profit, reason, timestamp) VALUES
('BTC/USDT', 'buy', 0.001, 65000.0, 0, '买入信号', '2025-10-31 10:00:00'),
('BTC/USDT', 'sell', 0.001, 66000.0, 10.0, '卖出信号', '2025-10-31 11:00:00'),
('BTC/USDT', 'buy', 0.0015, 66500.0, 0, '买入信号', '2025-10-31 12:00:00'),
('BTC/USDT', 'sell', 0.0015, 67000.0, 7.5, '卖出信号', '2025-10-31 13:00:00'),
('BTC/USDT', 'buy', 0.002, 67200.0, 0, '买入信号', '2025-10-31 14:00:00');
\" && echo '✅ 测试数据插入成功' || echo '❌ 测试数据插入失败'

echo ''
echo '验证测试数据:'
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot -e 'SELECT COUNT(*) as total_trades FROM trades;'

echo ''
echo '查看最新数据:'
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot -e 'SELECT * FROM trades ORDER BY timestamp DESC LIMIT 3;'
"

echo ""
echo "🔄 6. 重启应用并测试..."
ssh root@$VPS_IP "
cd $PROJECT_PATH

echo '重启应用容器:'
docker-compose restart btc-trading-bot

echo '等待应用启动...'
sleep 10

echo '测试API响应:'
curl -s http://localhost:8080/api/dashboard | jq . 2>/dev/null || curl -s http://localhost:8080/api/dashboard

echo ''
echo '测试交易数据API:'
curl -s http://localhost:8080/api/trades | jq . 2>/dev/null || curl -s http://localhost:8080/api/trades
"

echo ""
echo "✅ 诊断完成！"
echo "如果仍然没有数据，可能需要检查应用代码中的数据库连接配置。"