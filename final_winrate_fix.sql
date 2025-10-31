-- 最终胜率修复脚本
-- 删除所有现有记录并插入正确的测试数据

USE trading_bot;

-- 1. 清空所有交易记录
DELETE FROM trades;

-- 2. 重置自增ID
ALTER TABLE trades AUTO_INCREMENT = 1;

-- 3. 插入正确的测试数据（确保时间顺序正确）
-- 第一笔交易：盈利交易
INSERT INTO trades (timestamp, action, amount, price, reason) VALUES 
('2024-01-01 10:00:00', 'open_long', 0.001, 50000.0, '测试开仓1'),
('2024-01-01 10:05:00', 'close_long', 0.001, 51000.0, '止盈触发');

-- 第二笔交易：盈利交易  
INSERT INTO trades (timestamp, action, amount, price, reason) VALUES 
('2024-01-01 11:00:00', 'open_long', 0.001, 52000.0, '测试开仓2'),
('2024-01-01 11:05:00', 'close_long', 0.001, 53000.0, '止盈触发');

-- 4. 验证插入的数据
SELECT 'Current trades:' as info;
SELECT id, timestamp, action, amount, price, reason FROM trades ORDER BY timestamp;

-- 5. 计算预期结果
SELECT 'Expected results:' as info;
SELECT 
    '第一笔交易盈亏:' as description,
    (51000.0 - 50000.0) * 0.001 as pnl
UNION ALL
SELECT 
    '第二笔交易盈亏:' as description,
    (53000.0 - 52000.0) * 0.001 as pnl
UNION ALL
SELECT 
    '总盈亏:' as description,
    ((51000.0 - 50000.0) + (53000.0 - 52000.0)) * 0.001 as total_pnl
UNION ALL
SELECT 
    '预期胜率:' as description,
    100.0 as win_rate_percent;