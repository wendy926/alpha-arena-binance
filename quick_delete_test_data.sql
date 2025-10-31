-- 删除测试数据 (ID 1-4)
-- 保留真实交易数据 (ID 5)

USE trading_bot;

-- 查看删除前的数据
SELECT '删除前的数据:' as status;
SELECT id, timestamp, action, amount, price, reason FROM trades ORDER BY id ASC;

-- 删除测试数据
DELETE FROM trades WHERE id IN (1, 2, 3, 4);

-- 查看删除后的数据
SELECT '删除后的数据:' as status;
SELECT id, timestamp, action, amount, price, reason FROM trades ORDER BY id ASC;

-- 显示统计信息
SELECT '统计信息:' as status;
SELECT COUNT(*) as total_records FROM trades;