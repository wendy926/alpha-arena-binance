-- 调试胜率计算问题
USE trading_bot;

-- 1. 查看所有记录按时间排序
SELECT '=== 按时间排序的所有记录 ===' as status;
SELECT id, timestamp, action, amount, price, reason FROM trades ORDER BY timestamp ASC;

-- 2. 查看所有记录按ID排序  
SELECT '=== 按ID排序的所有记录 ===' as status;
SELECT id, timestamp, action, amount, price, reason FROM trades ORDER BY id ASC;

-- 3. 检查数据类型和值
SELECT '=== 数据类型检查 ===' as status;
SELECT 
  id,
  action,
  TYPEOF(price) as price_type,
  price,
  TYPEOF(amount) as amount_type, 
  amount,
  timestamp
FROM trades ORDER BY id ASC;

-- 4. 统计各种action的数量
SELECT '=== Action统计 ===' as status;
SELECT action, COUNT(*) as count FROM trades GROUP BY action;

-- 5. 检查是否有NULL值
SELECT '=== NULL值检查 ===' as status;
SELECT 
  COUNT(*) as total_records,
  SUM(CASE WHEN action IS NULL THEN 1 ELSE 0 END) as null_actions,
  SUM(CASE WHEN price IS NULL THEN 1 ELSE 0 END) as null_prices,
  SUM(CASE WHEN amount IS NULL THEN 1 ELSE 0 END) as null_amounts
FROM trades;