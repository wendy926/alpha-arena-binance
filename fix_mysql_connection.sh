#!/bin/bash

echo "🚀 MySQL连接问题快速修复"
echo "========================"

# 停止所有服务
echo "1. 停止所有Docker服务..."
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