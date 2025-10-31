#!/bin/bash

echo "🔧 初始化数据库表结构..."
echo "=================================="

# 创建数据库表结构的SQL脚本
cat > /tmp/init_tables.sql << 'EOF'
-- 创建交易记录表
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

-- 创建持仓记录表
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

-- 创建AI决策记录表
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

-- 创建账户信息表
CREATE TABLE IF NOT EXISTS account_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    available_balance DECIMAL(18, 8) DEFAULT 0.0,
    total_equity DECIMAL(18, 8) DEFAULT 0.0,
    leverage DECIMAL(5, 2) DEFAULT 1.0,
    margin_ratio DECIMAL(5, 4) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 插入默认配置
INSERT IGNORE INTO system_config (config_key, config_value, description) VALUES
('trading_mode', 'test', '交易模式：test/live'),
('initial_balance', '10000.0', '初始余额'),
('leverage', '1.0', '杠杆倍数'),
('risk_per_trade', '0.02', '每笔交易风险比例');

-- 显示创建的表
SHOW TABLES;

-- 显示表结构
DESCRIBE trades;
DESCRIBE positions;
EOF

echo "📋 执行数据库初始化脚本..."
docker-compose exec mysql mysql -u trader -ptrader123 trading_bot < /tmp/init_tables.sql

echo ""
echo "✅ 验证表创建结果："
docker-compose exec mysql mysql -u trader -ptrader123 -e "SHOW TABLES;" trading_bot

echo ""
echo "📊 检查表结构："
docker-compose exec mysql mysql -u trader -ptrader123 -e "DESCRIBE trades;" trading_bot

echo ""
echo "🔢 检查表记录数量："
docker-compose exec mysql mysql -u trader -ptrader123 -e "
SELECT 
    'trades' as table_name, COUNT(*) as record_count FROM trades
UNION ALL
SELECT 
    'positions' as table_name, COUNT(*) as record_count FROM positions
UNION ALL
SELECT 
    'ai_decisions' as table_name, COUNT(*) as record_count FROM ai_decisions;
" trading_bot

echo ""
echo "🎯 数据库表初始化完成！"