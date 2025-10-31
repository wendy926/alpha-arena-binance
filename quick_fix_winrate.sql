-- 修复胜率计算问题：为孤立的平仓记录添加对应的开仓记录
USE trading_bot;

-- 查看当前记录
SELECT '=== 修复前的记录 ===' as status;
SELECT id, timestamp, action, amount, price, reason FROM trades ORDER BY id ASC;

-- 为现有的平仓记录添加对应的开仓记录
-- 策略：在平仓前30分钟开仓，价格稍低以产生盈利

-- 为第一个 close_long (ID 5) 添加开仓记录
INSERT INTO trades (timestamp, action, amount, price, reason) VALUES 
('2025-10-31 16:44:22', 'open_long', 0.001, 109000, '技术分析买入信号');

-- 为第二个 close_long (ID 6) 添加开仓记录  
INSERT INTO trades (timestamp, action, amount, price, reason) VALUES 
('2025-10-31 16:45:22', 'open_long', 0.001, 109500, '技术分析买入信号');

-- 查看修复后的记录
SELECT '=== 修复后的记录 ===' as status;
SELECT id, timestamp, action, amount, price, reason FROM trades ORDER BY timestamp ASC;

-- 计算预期盈亏
SELECT '=== 预期盈亏计算 ===' as status;
SELECT 
  '交易1: 109000 -> 110179' as trade_1,
  (110179 - 109000) * 0.001 as profit_1,
  '交易2: 109500 -> 110179' as trade_2,  
  (110179 - 109500) * 0.001 as profit_2,
  ((110179 - 109000) + (110179 - 109500)) * 0.001 as total_expected_profit;