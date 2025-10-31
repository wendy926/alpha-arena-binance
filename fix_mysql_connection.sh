#!/bin/bash

echo "🔧 修复MySQL连接问题"
echo "=================================="

VPS_IP="47.79.95.72"
PROJECT_PATH="/opt/alpha-arena/alpha-arena-binance"

echo "📊 1. 检查MySQL Docker容器状态..."
ssh root@$VPS_IP "
echo '检查MySQL Docker容器:'
docker ps | grep mysql

echo ''
echo '检查容器健康状态:'
docker inspect alpha-arena-mysql --format='{{.State.Health.Status}}' 2>/dev/null || echo '无健康检查信息'

echo ''
echo '检查MySQL端口:'
netstat -tlnp | grep 3306 || ss -tlnp | grep 3306 || echo '端口3306未监听'
"

echo ""
echo "🧪 2. 测试MySQL连接..."
ssh root@$VPS_IP "
cd $PROJECT_PATH

echo '测试直接连接MySQL容器:'
docker exec alpha-arena-mysql mysql -u trader -ptrader123 -e 'SELECT 1;' 2>/dev/null && echo '✅ MySQL容器连接成功' || echo '❌ MySQL容器连接失败'

echo ''
echo '测试从应用容器连接MySQL:'
docker exec btc-trading-bot mysql -u trader -ptrader123 -h mysql -e 'SELECT 1;' 2>/dev/null && echo '✅ 应用容器MySQL连接成功' || echo '❌ 应用容器MySQL连接失败'

echo ''
echo '测试localhost连接（端口映射）:'
mysql -u trader -ptrader123 -h localhost -P 3306 -e 'SELECT 1;' 2>/dev/null && echo '✅ localhost连接成功' || echo '❌ localhost连接失败'
"

echo ""
echo "🔤 3. 修复中文编码..."
ssh root@$VPS_IP "
cd $PROJECT_PATH

echo '方法1: 通过MySQL容器直接修复编码:'
docker exec alpha-arena-mysql mysql -u trader -ptrader123 trading_bot -e \"
ALTER DATABASE trading_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE trades CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
UPDATE trades SET reason = '买入信号' WHERE reason LIKE '%买入%' OR reason LIKE '%buy%';
UPDATE trades SET reason = '卖出信号' WHERE reason LIKE '%卖出%' OR reason LIKE '%sell%';
UPDATE trades SET reason = '止损' WHERE reason LIKE '%止损%' OR reason LIKE '%stop%';
\" 2>/dev/null && echo '✅ 直接编码修复成功' || echo '❌ 直接编码修复失败'

echo ''
echo '方法2: 通过应用容器修复编码:'
docker exec btc-trading-bot mysql -u trader -ptrader123 -h mysql trading_bot -e \"
ALTER DATABASE trading_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE trades CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
UPDATE trades SET reason = '买入信号' WHERE reason LIKE '%买入%' OR reason LIKE '%buy%';
UPDATE trades SET reason = '卖出信号' WHERE reason LIKE '%卖出%' OR reason LIKE '%sell%';
UPDATE trades SET reason = '止损' WHERE reason LIKE '%止损%' OR reason LIKE '%stop%';
\" 2>/dev/null && echo '✅ 应用容器编码修复成功' || echo '❌ 应用容器编码修复失败'

echo ''
echo '方法3: 通过localhost端口映射修复编码:'
mysql -u trader -ptrader123 -h localhost -P 3306 trading_bot -e \"
ALTER DATABASE trading_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE trades CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
UPDATE trades SET reason = '买入信号' WHERE reason LIKE '%买入%' OR reason LIKE '%buy%';
UPDATE trades SET reason = '卖出信号' WHERE reason LIKE '%卖出%' OR reason LIKE '%sell%';
UPDATE trades SET reason = '止损' WHERE reason LIKE '%止损%' OR reason LIKE '%stop%';
\" 2>/dev/null && echo '✅ localhost编码修复成功' || echo '❌ localhost编码修复失败'
"

echo ""
echo "🔧 4. 开始修复MySQL连接问题..."
ssh root@$VPS_IP "
cd $PROJECT_PATH

# 停止所有服务
echo '停止所有Docker服务...'
docker-compose down

# 检查并清理可能的冲突
echo "2. 清理可能的端口冲突..."
pkill -f mysql 2>/dev/null || true
sleep 2

# 检查MySQL数据目录
echo "3. 检查MySQL数据目录..."
if [ ! -d "./mysql-data" ]; then
    echo "创建MySQL数据目录..."
    mkdir -p ./mysql-data
fi

# 修复权限
echo "4. 修复MySQL数据目录权限..."
chown -R 999:999 ./mysql-data 2>/dev/null || sudo chown -R 999:999 ./mysql-data
chmod -R 755 ./mysql-data

# 清理Docker网络和卷
echo "5. 清理Docker资源..."
docker network prune -f
docker volume prune -f

# 重新构建并启动MySQL
echo "6. 启动MySQL容器..."
docker-compose up -d mysql

# 等待启动
echo "7. 等待MySQL启动（45秒）..."
for i in {1..45}; do
    echo -n "."
    sleep 1
done
echo ""

# 检查状态
echo "8. 检查MySQL状态..."
if docker-compose ps mysql | grep -q "Up"; then
    echo "✅ MySQL容器启动成功！"
    
    # 等待MySQL服务就绪
    echo "9. 等待MySQL服务就绪..."
    for i in {1..30}; do
        if docker-compose exec mysql mysqladmin ping -h localhost 2>/dev/null; then
            echo "✅ MySQL服务就绪！"
            break
        fi
        echo -n "."
        sleep 2
    done
    echo ""
    
    # 启动完整服务
    echo "10. 启动完整服务..."
    docker-compose up -d
    
    echo ""
    echo "🎉 修复完成！服务状态:"
    docker-compose ps
    
else
    echo "❌ MySQL启动失败，查看日志:"
    docker-compose logs mysql | tail -20
    
    echo ""
    echo "💡 尝试重置MySQL数据:"
    echo "rm -rf ./mysql-data && mkdir ./mysql-data && chown -R 999:999 ./mysql-data"
fi

# 重新启动所有服务
echo '重新启动所有Docker服务...'
docker-compose up -d

echo '等待服务启动...'
sleep 20

echo '检查服务状态:'
docker ps | grep -E '(mysql|btc-trading-bot)'
"

echo ""
echo "🔄 5. 重启应用容器..."
ssh root@$VPS_IP "
cd $PROJECT_PATH
docker-compose restart btc-trading-bot
"

echo ""
echo "⏳ 等待应用启动..."
sleep 15

echo ""
echo "🧪 6. 最终测试..."
ssh root@$VPS_IP "
cd $PROJECT_PATH

echo '最终MySQL连接测试:'
docker exec alpha-arena-mysql mysql -u trader -ptrader123 -e 'SELECT 1;' 2>/dev/null && echo '✅ MySQL最终测试成功' || echo '❌ MySQL最终测试失败'

echo ''
echo '测试API端点:'
curl -s http://localhost:8080/api/dashboard | head -200

echo ''
echo ''
echo '测试交易数据:'
curl -s http://localhost:8080/api/trades | head -200

echo ''
echo '检查应用日志:'
docker logs btc-trading-bot --tail 10
"

echo ""
echo "✅ MySQL修复完成！"
echo "请访问 https://arena.aimaventop.com/flow/ 查看修复结果"