#!/bin/bash

echo "🔧 VPS数据库修复脚本 (修复TTY问题)"
echo "=================================="

# 检查容器状态
echo "📊 检查容器状态："
docker-compose ps

# 1. 使用 -T 参数避免TTY问题，创建数据库表结构
echo "🔧 创建数据库表结构..."

# 直接执行SQL命令，避免文件重定向问题
docker-compose exec -T mysql mysql -u trader -ptrader123 trading_bot -e "
CREATE TABLE IF NOT EXISTS trades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    symbol VARCHAR(20) NOT NULL DEFAULT 'BTC/USDT',
    side VARCHAR(10) NOT NULL,
    amount DECIMAL(18, 8) NOT NULL,
    price DECIMAL(18, 8) NOT NULL,
    total_value DECIMAL(18, 8) NOT NULL,
    confidence DECIMAL(5, 2) DEFAULT 0.0,
    reason TEXT,
    profit_loss DECIMAL(18, 8) DEFAULT 0.0,
    status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS positions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL DEFAULT 'BTC/USDT',
    side VARCHAR(10) NOT NULL,
    amount DECIMAL(18, 8) NOT NULL,
    entry_price DECIMAL(18, 8) NOT NULL,
    current_price DECIMAL(18, 8) DEFAULT 0.0,
    unrealized_pnl DECIMAL(18, 8) DEFAULT 0.0,
    is_active BOOLEAN DEFAULT TRUE,
    opened_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    closed_at DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_decisions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    symbol VARCHAR(20) NOT NULL DEFAULT 'BTC/USDT',
    decision VARCHAR(20) NOT NULL,
    confidence DECIMAL(5, 2) DEFAULT 0.0,
    reason TEXT,
    price DECIMAL(18, 8) NOT NULL,
    stop_loss DECIMAL(18, 8) DEFAULT 0.0,
    take_profit DECIMAL(18, 8) DEFAULT 0.0,
    executed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

SHOW TABLES;"

echo "✅ 数据库表创建完成"
echo ""

# 2. 插入测试数据
echo "📊 创建测试数据..."

docker-compose exec -T mysql mysql -u trader -ptrader123 trading_bot -e "
INSERT INTO trades (timestamp, symbol, side, amount, price, total_value, confidence, reason, profit_loss, status) VALUES
('2025-10-31 10:00:00', 'BTC/USDT', 'buy', 0.1, 68500.00, 6850.00, 85.5, 'AI分析显示强烈买入信号', 0.0, 'completed'),
('2025-10-31 11:30:00', 'BTC/USDT', 'sell', 0.1, 69200.00, 6920.00, 78.2, '达到止盈目标', 70.00, 'completed'),
('2025-10-31 13:15:00', 'BTC/USDT', 'buy', 0.15, 68800.00, 10320.00, 82.1, '回调买入机会', 0.0, 'completed'),
('2025-10-31 14:45:00', 'BTC/USDT', 'sell', 0.15, 69500.00, 10425.00, 88.7, '突破阻力位', 105.00, 'completed');

INSERT INTO positions (symbol, side, amount, entry_price, current_price, unrealized_pnl, is_active, opened_at) VALUES
('BTC/USDT', 'long', 0.2, 69300.00, 69450.00, 30.00, TRUE, '2025-10-31 15:00:00');

INSERT INTO ai_decisions (timestamp, symbol, decision, confidence, reason, price, stop_loss, take_profit, executed) VALUES
('2025-10-31 15:05:00', 'BTC/USDT', 'hold', 72.5, '当前趋势不明确，建议持有观望', 69450.00, 68500.00, 70500.00, FALSE);"

echo "✅ 测试数据创建完成"
echo ""

# 3. 验证数据
echo "📋 验证数据："
echo "交易记录数量："
docker-compose exec -T mysql mysql -u trader -ptrader123 -e "SELECT COUNT(*) as trades_count FROM trades;" trading_bot

echo "持仓记录："
docker-compose exec -T mysql mysql -u trader -ptrader123 -e "SELECT * FROM positions WHERE is_active = 1;" trading_bot

echo "AI决策："
docker-compose exec -T mysql mysql -u trader -ptrader123 -e "SELECT * FROM ai_decisions ORDER BY timestamp DESC LIMIT 1;" trading_bot

# 4. 重启应用
echo "🔄 重启应用..."
docker-compose restart btc-trading-bot

# 5. 等待并测试
echo "⏳ 等待应用重启（15秒）..."
sleep 15

echo "🌐 测试API响应："
curl -s http://localhost:8080/api/trades | head -100
echo ""
curl -s http://localhost:8080/api/dashboard | head -100

echo ""
echo "✅ 数据库修复完成！现在可以访问 http://47.79.95.72:8080 查看数据了！"