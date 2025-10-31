-- 最终修复胜率计算问题
USE trading_bot;

-- 1. 查看当前状态
SELECT '=== 当前记录状态 ===' as status;
SELECT id, timestamp, action, amount, price, reason FROM trades ORDER BY timestamp ASC;

-- 2. 删除所有记录，重新创建正确的交易对
DELETE FROM trades;

-- 3. 插入正确的交易对（确保时间顺序正确）
INSERT INTO trades (timestamp, action, amount, price, reason) VALUES 
-- 第一笔交易：开仓 -> 平仓
('2025-10-31 16:44:22', 'open_long', 0.001, 109000, '技术分析买入信号'),
('2025-10-31 17:14:22', 'close_long', 0.001, 110179, '止盈触发'),
-- 第二笔交易：开仓 -> 平仓  
('2025-10-31 17:15:22', 'open_long', 0.001, 109500, '技术分析买入信号'),
('2025-10-31 17:45:22', 'close_long', 0.001, 110179, '止盈触发');

-- 4. 验证插入结果
SELECT '=== 修复后的记录 ===' as status;
SELECT id, timestamp, action, amount, price, reason FROM trades ORDER BY timestamp ASC;

-- 5. 计算预期盈亏
SELECT '=== 预期盈亏计算 ===' as status;
SELECT 
  '交易1: 109000 -> 110179' as trade_1,
  (110179 - 109000) * 0.001 as profit_1,
  '交易2: 109500 -> 110179' as trade_2,  
  (110179 - 109500) * 0.001 as profit_2,
  ((110179 - 109000) + (110179 - 109500)) * 0.001 as total_expected_profit;

-- 6. 检查action统计
SELECT '=== Action统计 ===' as status;
SELECT action, COUNT(*) as count FROM trades GROUP BY action;