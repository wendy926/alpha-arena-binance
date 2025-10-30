#!/bin/bash

echo "🔄 等待MySQL完全启动..."
echo "========================"

echo "步骤1: 检查MySQL容器状态..."
docker-compose ps mysql

echo ""
echo "步骤2: 等待MySQL完全启动（最多60秒）..."
for i in {1..12}; do
    echo "等待中... $(($i * 5))秒"
    
    # 检查MySQL是否准备就绪
    if docker-compose exec mysql mysqladmin ping -h localhost --silent 2>/dev/null; then
        echo "✅ MySQL连接成功！"
        break
    fi
    
    if [ $i -eq 12 ]; then
        echo "❌ MySQL启动超时"
        echo "显示最新日志:"
        docker-compose logs mysql | tail -10
        exit 1
    fi
    
    sleep 5
done

echo ""
echo "步骤3: 测试MySQL数据库操作..."
if docker-compose exec mysql mysql -h localhost -u root -proot123 -e "SELECT 1;" 2>/dev/null; then
    echo "✅ MySQL数据库连接成功！"
else
    echo "❌ MySQL数据库连接失败"
    echo "尝试无密码连接..."
    if docker-compose exec mysql mysql -h localhost -u root -e "SELECT 1;" 2>/dev/null; then
        echo "✅ MySQL无密码连接成功！"
        echo "⚠️  注意：MySQL root用户没有密码"
    else
        echo "❌ 所有连接方式都失败"
        docker-compose logs mysql | tail -15
        exit 1
    fi
fi

echo ""
echo "步骤4: 启动完整服务..."
docker-compose up -d

echo ""
echo "步骤5: 检查所有服务状态..."
docker-compose ps

echo ""
echo "🎉 MySQL已准备就绪！现在可以运行数据恢复:"
echo "python3 restore_data_docker.py"