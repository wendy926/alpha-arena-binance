#!/bin/bash

# 简化版数据库修复脚本，避免TTY问题
# 使用方法: 在VPS上执行 bash vps_fix_simple.sh

echo "🔧 简化版数据库修复脚本"
echo "=================================="

# 创建trades表
echo "📋 创建trades表..."
docker-compose exec -T mysql mysql -u trader -ptrader123 -e "
USE trading_bot;
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
  status VARCHAR(20) DEFAULT 'completed'
);"

# 创建positions表
echo "📋 创建positions表..."
docker-compose exec -T mysql mysql -u trader -ptrader123 -e "
USE trading_bot;
CREATE TABLE IF NOT EXISTS positions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  symbol VARCHAR(20) NOT NULL DEFAULT 'BTC/USDT',
  side VARCHAR(10) NOT NULL,
  amount DECIMAL(18, 8) NOT NULL,
  entry_price DECIMAL(18, 8) NOT NULL,
  current_price DECIMAL(18, 8) DEFAULT 0.0,
  unrealized_pnl DECIMAL(18, 8) DEFAULT 0.0,
  is_active BOOLEAN DEFAULT TRUE,
  opened_at DATETIME DEFAULT CURRENT_TIMESTAMP
);"

# 创建ai_decisions表
echo "📋 创建ai_decisions表..."
docker-compose exec -T mysql mysql -u trader -ptrader123 -e "
USE trading_bot;
CREATE TABLE IF NOT EXISTS ai_decisions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  symbol VARCHAR(20) NOT NULL DEFAULT 'BTC/USDT',
  decision VARCHAR(20) NOT NULL,
  confidence DECIMAL(5, 2) DEFAULT 0.0,
  reason TEXT,
  price DECIMAL(18, 8) NOT NULL,
  executed BOOLEAN DEFAULT FALSE
);"

# 检查表是否创建成功
echo "✅ 检查表是否创建成功..."
docker-compose exec -T mysql mysql -u trader -ptrader123 -e "
USE trading_bot;
SHOW TABLES;"

# 插入测试交易数据
echo "📊 插入测试交易数据..."
docker-compose exec -T mysql mysql -u trader -ptrader123 -e "
USE trading_bot;
INSERT INTO trades (timestamp, symbol, side, amount, price, total_value, confidence, reason, profit_loss) VALUES
('2025-10-31 10:00:00', 'BTC/USDT', 'buy', 0.1, 68500.00, 6850.00, 85.5, 'AI买入信号', 0.0),
('2025-10-31 11:30:00', 'BTC/USDT', 'sell', 0.1, 69200.00, 6920.00, 78.2, '止盈', 70.00),
('2025-10-31 13:15:00', 'BTC/USDT', 'buy', 0.15, 68800.00, 10320.00, 82.1, '回调买入', 0.0),
('2025-10-31 14:45:00', 'BTC/USDT', 'sell', 0.15, 69500.00, 10425.00, 88.7, '突破卖出', 105.00);"

# 插入测试持仓数据
echo "📊 插入测试持仓数据..."
docker-compose exec -T mysql mysql -u trader -ptrader123 -e "
USE trading_bot;
INSERT INTO positions (symbol, side, amount, entry_price, current_price, unrealized_pnl, is_active) VALUES
('BTC/USDT', 'long', 0.2, 69300.00, 69450.00, 30.00, TRUE);"

# 插入测试AI决策数据
echo "📊 插入测试AI决策数据..."
docker-compose exec -T mysql mysql -u trader -ptrader123 -e "
USE trading_bot;
INSERT INTO ai_decisions (symbol, decision, confidence, reason, price) VALUES
('BTC/USDT', 'hold', 72.5, '趋势不明确，持有观望', 69450.00);"

# 验证数据
echo "✅ 验证数据..."
echo "交易记录数量："
docker-compose exec -T mysql mysql -u trader -ptrader123 -e "
USE trading_bot;
SELECT COUNT(*) as trades_count FROM trades;"

echo "持仓记录："
docker-compose exec -T mysql mysql -u trader -ptrader123 -e "
USE trading_bot;
SELECT * FROM positions WHERE is_active = 1;"

# 重启应用
echo "🔄 重启应用..."
docker-compose restart btc-trading-bot

# 等待应用重启
echo "⏳ 等待应用重启（15秒）..."
sleep 15

# 测试API
echo "🌐 测试API响应："
curl -s http://localhost:8080/api/trades | head -50

echo ""
echo "✅ 数据库修复完成！现在可以访问 http://47.79.95.72:8080 查看数据了！"