#!/bin/bash

echo "⏳ 等待MySQL健康检查通过..."
echo "============================="

echo "步骤1: 检查MySQL容器当前状态..."
docker-compose ps mysql

echo ""
echo "步骤2: 等待MySQL健康检查通过（最多120秒）..."
for i in {1..24}; do
    echo "检查第 $i 次 ($(($i * 5))秒)..."
    
    # 检查容器健康状态
    health_status=$(docker-compose ps mysql --format "table {{.Status}}" | tail -n 1)
    echo "容器状态: $health_status"
    
    # 检查是否包含 "healthy" 状态
    if echo "$health_status" | grep -q "healthy"; then
        echo "✅ MySQL健康检查通过！"
        break
    fi
    
    # 检查是否仍在启动中
    if echo "$health_status" | grep -q "starting"; then
        echo "🔄 MySQL仍在启动中，继续等待..."
    elif echo "$health_status" | grep -q "unhealthy"; then
        echo "❌ MySQL健康检查失败"
        echo "显示MySQL日志:"
        docker-compose logs mysql | tail -20
        exit 1
    fi
    
    # 如果是最后一次检查
    if [ $i -eq 24 ]; then
        echo "❌ MySQL启动超时（120秒）"
        echo "显示MySQL日志:"
        docker-compose logs mysql | tail -20
        exit 1
    fi
    
    sleep 5
done

echo ""
echo "步骤3: 测试MySQL连接..."
if docker-compose exec mysql mysqladmin ping -h localhost --silent 2>/dev/null; then
    echo "✅ MySQL ping测试成功！"
else
    echo "⚠️  MySQL ping失败，但容器健康，尝试直接连接..."
fi

echo ""
echo "步骤4: 测试MySQL数据库连接..."
# 尝试不同的连接方式
if docker-compose exec mysql mysql -h localhost -u root -e "SELECT 1;" 2>/dev/null; then
    echo "✅ MySQL无密码连接成功！"
    mysql_password=""
elif docker-compose exec mysql mysql -h localhost -u root -proot123 -e "SELECT 1;" 2>/dev/null; then
    echo "✅ MySQL密码连接成功！"
    mysql_password="root123"
else
    echo "❌ MySQL连接失败"
    echo "显示连接错误信息:"
    docker-compose exec mysql mysql -h localhost -u root -e "SELECT 1;"
    exit 1
fi

echo ""
echo "步骤5: 启动完整服务..."
docker-compose up -d

echo ""
echo "步骤6: 检查所有服务状态..."
docker-compose ps

echo ""
echo "🎉 MySQL已完全就绪！开始恢复数据..."
echo "=================================="

# 运行数据恢复脚本
python3 restore_data_docker.py

echo ""
echo "✅ 数据恢复完成！可以访问前端查看结果"