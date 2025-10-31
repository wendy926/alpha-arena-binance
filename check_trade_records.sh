#!/bin/bash

echo "🔍 检查数据库交易记录详情"
echo "=========================="

echo "📊 1. 总记录数:"
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot -e "SELECT COUNT(*) as total_records FROM trades;"

echo -e "\n📋 2. 所有交易记录:"
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot -e "
SELECT id, timestamp, action, amount, price, reason 
FROM trades 
ORDER BY id ASC;
"

echo -e "\n📈 3. 按操作类型分组统计:"
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot -e "
SELECT action, COUNT(*) as count 
FROM trades 
GROUP BY action 
ORDER BY action;
"

echo -e "\n🎯 4. 胜率计算逻辑分析:"
echo "   - 开仓操作 (open_long/open_short): 开始一笔交易"
echo "   - 平仓操作 (close_long/close_short): 完成一笔交易"
echo "   - 完整交易数 = 平仓操作数量"
echo "   - 胜率 = 盈利的平仓操作 / 总平仓操作"

echo -e "\n📊 5. 完整交易配对分析:"
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot -e "
SELECT 
    'open_operations' as type, 
    COUNT(*) as count 
FROM trades 
WHERE action IN ('open_long', 'open_short')
UNION ALL
SELECT 
    'close_operations' as type, 
    COUNT(*) as count 
FROM trades 
WHERE action IN ('close_long', 'close_short');
"