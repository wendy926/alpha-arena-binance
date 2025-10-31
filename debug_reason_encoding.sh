#!/bin/bash

echo "🔍 调试reason字段编码问题"
echo "=========================="

echo "📊 1. 检查数据库字符集设置:"
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot -e "
SHOW VARIABLES LIKE 'character_set%';
SHOW VARIABLES LIKE 'collation%';
"

echo -e "\n📋 2. 检查trades表结构和字符集:"
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot -e "
SHOW CREATE TABLE trades;
"

echo -e "\n🔍 3. 查看第5条记录的原始数据 (使用HEX):"
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot -e "
SELECT id, timestamp, action, HEX(reason) as reason_hex, CHAR_LENGTH(reason) as reason_length 
FROM trades 
WHERE id = 5;
"

echo -e "\n📝 4. 查看所有记录的reason字段长度和内容:"
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot -e "
SELECT id, action, reason, CHAR_LENGTH(reason) as length, LENGTH(reason) as byte_length 
FROM trades 
ORDER BY id ASC;
"

echo -e "\n🔧 5. 尝试修复第5条记录的reason字段:"
echo "   如果reason包含特殊字符，我们可以更新它"

echo -e "\n💡 6. 检查应用日志中的AI响应:"
echo "   查看最近的AI响应是否包含特殊字符"
docker logs btc-trading-bot 2>&1 | grep -A 5 -B 5 "AI响应\|reason" | tail -20

echo -e "\n🎯 7. 建议的修复方案:"
echo "   1. 更新数据库字符集为utf8mb4"
echo "   2. 修复第5条记录的reason字段"
echo "   3. 在代码中添加字符编码处理"