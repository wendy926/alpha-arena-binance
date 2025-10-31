#!/bin/bash

echo "🔍 检查数据库记录和调试胜率计算"
echo "================================"

echo "📊 1. 查看当前数据库记录:"
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot --default-character-set=utf8mb4 -e "
SELECT id, timestamp, action, amount, price, reason 
FROM trades 
ORDER BY timestamp ASC;
"

echo -e "\n📋 2. 检查数据类型和统计:"
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot -e "
SELECT 
  COUNT(*) as total_records,
  COUNT(CASE WHEN action = 'open_long' THEN 1 END) as open_long_count,
  COUNT(CASE WHEN action = 'close_long' THEN 1 END) as close_long_count,
  COUNT(CASE WHEN action = 'open_short' THEN 1 END) as open_short_count,
  COUNT(CASE WHEN action = 'close_short' THEN 1 END) as close_short_count
FROM trades;
"

echo -e "\n🔍 3. 检查数据完整性:"
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot -e "
SELECT 
  id,
  action,
  price,
  amount,
  CASE 
    WHEN price IS NULL THEN 'NULL'
    WHEN price = '' THEN 'EMPTY'
    WHEN price = 0 THEN 'ZERO'
    ELSE 'VALID'
  END as price_status,
  CASE 
    WHEN amount IS NULL THEN 'NULL'
    WHEN amount = '' THEN 'EMPTY' 
    WHEN amount = 0 THEN 'ZERO'
    ELSE 'VALID'
  END as amount_status
FROM trades 
ORDER BY timestamp ASC;
"

echo -e "\n🧪 4. 运行Python调试脚本:"
cd /root/alpha-arena-binance
python3 debug_compute_winrate.py

echo -e "\n🔄 5. 检查应用日志:"
echo "最近的应用日志:"
docker logs btc-trading-bot --tail 20

echo -e "\n💡 6. 可能的问题:"
echo "   1. 数据库字段类型问题"
echo "   2. 胜率计算函数中的逻辑错误"
echo "   3. 数据库连接或查询问题"
echo "   4. Python模块导入问题"

echo -e "\n✅ 检查完成！"