#!/bin/bash

echo "📊 创建测试数据..."
echo "=================================="

# 创建测试数据的SQL脚本
cat > /tmp/test_data.sql << 'EOF'
-- 插入测试交易记录
INSERT INTO trades (timestamp, symbol, side, amount, price, total_value, confidence, reason, profit_loss, status) VALUES
('2025-10-31 10:00:00', 'BTC/USDT', 'buy', 0.1, 68500.00, 6850.00, 85.5, 'AI分析显示强烈买入信号，技术指标看涨', 0.0, 'completed'),
('2025-10-31 11:30:00', 'BTC/USDT', 'sell', 0.1, 69200.00, 6920.00, 78.2, '达到止盈目标，获利了结', 70.00, 'completed'),
('2025-10-31 13:15:00', 'BTC/USDT', 'buy', 0.15, 68800.00, 10320.00, 82.1, '回调买入机会，支撑位强劲', 0.0, 'completed'),
('2025-10-31 14:45:00', 'BTC/USDT', 'sell', 0.15, 69500.00, 10425.00, 88.7, '突破阻力位，趋势反转信号', 105.00, 'completed'),
('2025-10-31 15:00:00', 'BTC/USDT', 'buy', 0.2, 69300.00, 13860.00, 75.3, '短期调整后的买入机会', 0.0, 'pending');

-- 插入当前持仓（模拟有一个活跃持仓）
INSERT INTO positions (symbol, side, amount, entry_price, current_price, unrealized_pnl, is_active, opened_at) VALUES
('BTC/USDT', 'long', 0.2, 69300.00, 69450.00, 30.00, TRUE, '2025-10-31 15:00:00');

-- 插入AI决策记录
INSERT INTO ai_decisions (timestamp, symbol, decision, confidence, reason, price, stop_loss, take_profit, executed) VALUES
('2025-10-31 15:05:00', 'BTC/USDT', 'hold', 72.5, '当前趋势不明确，建议持有观望', 69450.00, 68500.00, 70500.00, FALSE),
('2025-10-31 15:04:00', 'BTC/USDT', 'buy', 75.3, '技术指标显示买入信号', 69300.00, 68500.00, 70200.00, TRUE),
('2025-10-31 14:45:00', 'BTC/USDT', 'sell', 88.7, '突破阻力位，建议获利了结', 69500.00, 0.00, 0.00, TRUE);

-- 插入账户信息
INSERT INTO account_info (timestamp, available_balance, total_equity, leverage, margin_ratio) VALUES
('2025-10-31 15:05:00', 8825.00, 10000.00, 1.0, 0.1386);

-- 更新系统配置
UPDATE system_config SET config_value = '10000.0' WHERE config_key = 'initial_balance';
UPDATE system_config SET config_value = 'test' WHERE config_key = 'trading_mode';
EOF

echo "📋 插入测试数据..."
docker-compose exec mysql mysql -u trader -ptrader123 trading_bot < /tmp/test_data.sql

echo ""
echo "✅ 验证数据插入结果："

echo "📈 交易记录数量："
docker-compose exec mysql mysql -u trader -ptrader123 -e "SELECT COUNT(*) as total_trades FROM trades;" trading_bot

echo ""
echo "💰 持仓记录："
docker-compose exec mysql mysql -u trader -ptrader123 -e "SELECT * FROM positions WHERE is_active = 1;" trading_bot

echo ""
echo "🤖 最新AI决策："
docker-compose exec mysql mysql -u trader -ptrader123 -e "SELECT * FROM ai_decisions ORDER BY timestamp DESC LIMIT 3;" trading_bot

echo ""
echo "📊 账户信息："
docker-compose exec mysql mysql -u trader -ptrader123 -e "SELECT * FROM account_info ORDER BY timestamp DESC LIMIT 1;" trading_bot

echo ""
echo "🎯 测试数据创建完成！"

echo ""
echo "🌐 测试API响应："
curl -s http://localhost:8080/api/trades | head -200

echo ""
echo "🔄 重启应用以刷新缓存："
docker-compose restart btc-trading-bot

echo ""
echo "⏳ 等待应用重启（10秒）..."
sleep 10

echo ""
echo "✅ 现在可以访问网站查看数据了！"