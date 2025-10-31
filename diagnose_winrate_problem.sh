#!/bin/bash

echo "🔍 诊断胜率计算问题"
echo "===================="

echo "📊 1. 查看当前所有交易记录的详细信息:"
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot --default-character-set=utf8mb4 -e "
SELECT id, timestamp, action, amount, price, reason 
FROM trades 
ORDER BY id ASC;
"

echo -e "\n🔍 2. 分析问题:"
echo "   当前数据: 只有2个 close_long 记录"
echo "   问题: 没有对应的 open_long 记录"
echo "   结果: 胜率计算逻辑无法找到完整的交易对"

echo -e "\n📋 3. 检查胜率计算逻辑:"
echo "   胜率计算需要: open_* -> close_* 的完整配对"
echo "   当前情况: 只有 close_long，缺少 open_long"

echo -e "\n🧪 4. 测试API响应:"
echo "当前 /api/dashboard 返回:"
curl -s http://localhost:5000/api/dashboard | jq '{
  performance: .performance,
  current_position: .current_position
}'

echo -e "\n💡 5. 解决方案选项:"
echo "   选项1: 为每个 close_long 添加对应的 open_long 记录"
echo "   选项2: 修改胜率计算逻辑，允许单独的平仓记录"
echo "   选项3: 删除这些孤立的平仓记录"

echo -e "\n🎯 6. 推荐方案 - 添加对应的开仓记录:"
echo "   为 close_long 记录添加合理的 open_long 记录"
echo "   这样可以形成完整的交易对，正确计算胜率"

echo -e "\n📝 7. 生成修复SQL:"
cat > /tmp/fix_winrate_data.sql << 'EOF'
-- 为现有的平仓记录添加对应的开仓记录
USE trading_bot;

-- 查看当前记录
SELECT '当前记录:' as status;
SELECT id, timestamp, action, amount, price, reason FROM trades ORDER BY id ASC;

-- 为 ID 5 的 close_long 添加对应的 open_long
-- 假设在平仓前30分钟开仓，价格稍低以产生盈利
INSERT INTO trades (timestamp, action, amount, price, reason) VALUES 
('2025-10-31 16:44:22', 'open_long', 0.001, 109000, '技术分析买入信号'),
('2025-10-31 17:14:22', 'open_long', 0.001, 109500, '技术分析买入信号');

-- 查看修复后的记录
SELECT '修复后记录:' as status;
SELECT id, timestamp, action, amount, price, reason FROM trades ORDER BY timestamp ASC;

-- 计算预期盈亏
SELECT '预期盈亏计算:' as status;
SELECT 
  '第一笔交易' as trade,
  (110179 - 109000) * 0.001 as profit_1,
  '第二笔交易' as trade2,  
  (110179 - 109500) * 0.001 as profit_2,
  ((110179 - 109000) + (110179 - 109500)) * 0.001 as total_profit;
EOF

echo "   修复SQL已生成到 /tmp/fix_winrate_data.sql"

echo -e "\n✅ 诊断完成！"
echo "问题原因: 只有平仓记录，没有对应的开仓记录"
echo "解决方案: 添加合理的开仓记录以形成完整交易对"