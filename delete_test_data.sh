#!/bin/bash

echo "🗑️ 删除交易中的测试数据"
echo "=========================="

echo "📊 1. 查看当前所有交易记录:"
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot -e "
SELECT id, timestamp, action, amount, price, reason 
FROM trades 
ORDER BY id ASC;
"

echo -e "\n🎯 2. 识别测试数据 vs 真实数据:"
echo "   测试数据: ID 1-4 (2025-10-31 的固定时间戳)"
echo "   真实数据: ID 5 (2025-10-31 17:14:22 的实际交易)"

echo -e "\n⚠️ 3. 备份当前数据 (以防需要恢复):"
docker exec alpha-arena-mysql mysqldump -u trader -ptrader123 trading_bot trades > /tmp/trades_backup_$(date +%Y%m%d_%H%M%S).sql
echo "   备份已保存到 /tmp/trades_backup_*.sql"

echo -e "\n🗑️ 4. 删除测试数据 (ID 1-4):"
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot -e "
DELETE FROM trades WHERE id IN (1, 2, 3, 4);
"

echo -e "\n✅ 5. 验证删除结果:"
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot -e "
SELECT COUNT(*) as total_records FROM trades;
"

echo -e "\n📋 6. 查看剩余的交易记录:"
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot --default-character-set=utf8mb4 -e "
SELECT id, timestamp, action, amount, price, reason 
FROM trades 
ORDER BY id ASC;
"

echo -e "\n🔄 7. 重启应用容器:"
docker restart btc-trading-bot
sleep 10

echo -e "\n🧪 8. 测试API端点:"
echo "测试 /api/dashboard:"
curl -s http://localhost:5000/api/dashboard | jq '{
  current_position: .current_position,
  performance: .performance
}'

echo -e "\n测试 /api/trades:"
curl -s http://localhost:5000/api/trades | jq 'length'

echo -e "\n📊 9. 预期结果:"
echo "   - 数据库只剩1条记录 (真实交易)"
echo "   - 胜率: 无法计算 (需要完整的开仓->平仓配对)"
echo "   - 总交易次数: 0 (只有平仓，没有对应的开仓)"
echo "   - 总利润: 0"

echo -e "\n💡 10. 注意事项:"
echo "   删除测试数据后，由于只剩下一个平仓操作，"
echo "   胜率计算可能会显示异常，这是正常的。"
echo "   如需正常显示，建议添加对应的开仓记录。"

echo -e "\n✅ 删除完成！"
echo "📱 访问网站查看结果: https://arena.aimaventop.com/flow/"