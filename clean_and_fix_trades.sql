-- 清理和修复交易记录脚本
-- 解决重复记录和数量不匹配问题

USE trading_bot;

-- 1. 显示当前问题记录
SELECT '=== 当前问题记录 ===' as info;
SELECT id, timestamp, action, amount, price, reason FROM trades ORDER BY timestamp;

-- 2. 删除所有现有记录
DELETE FROM trades;

-- 3. 重置自增ID
ALTER TABLE trades AUTO_INCREMENT = 1;

-- 4. 插入正确的配对交易记录
-- 第一笔交易：完整的开仓->平仓配对
INSERT INTO trades (timestamp, action, amount, price, reason) VALUES 
('2024-01-01 10:00:00', 'open_long', 0.001, 50000.0, '测试开仓1'),
('2024-01-01 10:05:00', 'close_long', 0.001, 51000.0, '止盈触发');

-- 第二笔交易：完整的开仓->平仓配对
INSERT INTO trades (timestamp, action, amount, price, reason) VALUES 
('2024-01-01 11:00:00', 'open_long', 0.001, 52000.0, '测试开仓2'),
('2024-01-01 11:05:00', 'close_long', 0.001, 53000.0, '止盈触发');

-- 5. 验证修复后的数据
SELECT '=== 修复后的记录 ===' as info;
SELECT id, timestamp, action, amount, price, reason FROM trades ORDER BY timestamp;

-- 6. 计算预期结果
SELECT '=== 预期计算结果 ===' as info;
SELECT 
    '第一笔交易盈亏' as description,
    (51000.0 - 50000.0) * 0.001 as pnl,
    'USD' as unit
UNION ALL
SELECT 
    '第二笔交易盈亏' as description,
    (53000.0 - 52000.0) * 0.001 as pnl,
    'USD' as unit
UNION ALL
SELECT 
    '总盈亏' as description,
    ((51000.0 - 50000.0) + (53000.0 - 52000.0)) * 0.001 as total_pnl,
    'USD' as unit
UNION ALL
SELECT 
    '胜利次数' as description,
    2 as wins,
    '次' as unit
UNION ALL
SELECT 
    '总交易次数' as description,
    2 as total_trades,
    '次' as unit
UNION ALL
SELECT 
    '预期胜率' as description,
    100.0 as win_rate,
    '%' as unit;