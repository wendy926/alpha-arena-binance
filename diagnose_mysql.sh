#!/bin/bash

echo "🔍 MySQL连接问题诊断脚本"
echo "=========================="

# 1. 检查Docker服务状态
echo "1. 检查Docker服务状态..."
systemctl status docker | head -5

echo ""
echo "2. 检查Docker Compose服务状态..."
docker-compose ps

echo ""
echo "3. 检查MySQL容器详细状态..."
docker-compose ps mysql
docker inspect $(docker-compose ps -q mysql) 2>/dev/null | grep -A 5 "State" || echo "MySQL容器不存在"

echo ""
echo "4. 检查MySQL容器日志..."
echo "最近20行MySQL日志:"
docker-compose logs --tail=20 mysql

echo ""
echo "5. 检查端口占用..."
netstat -tlnp | grep :3306 || echo "端口3306未被占用"

echo ""
echo "6. 检查MySQL数据目录..."
if [ -d "./mysql-data" ]; then
    echo "MySQL数据目录存在:"
    ls -la ./mysql-data | head -10
    echo "数据目录权限:"
    stat ./mysql-data
else
    echo "❌ MySQL数据目录不存在"
fi

echo ""
echo "7. 尝试重启MySQL容器..."
docker-compose stop mysql
sleep 5
docker-compose up -d mysql

echo ""
echo "8. 等待MySQL启动（30秒）..."
sleep 30

echo ""
echo "9. 再次检查MySQL状态..."
docker-compose ps mysql

echo ""
echo "10. 测试MySQL连接..."
if docker-compose exec mysql mysqladmin ping -h localhost -u alpha -palpha_pwd_2025 2>/dev/null; then
    echo "✅ MySQL连接成功！"
    echo "数据库列表:"
    docker-compose exec mysql mysql -u alpha -palpha_pwd_2025 -e "SHOW DATABASES;"
else
    echo "❌ MySQL连接仍然失败"
    echo "详细错误日志:"
    docker-compose logs mysql | tail -30
fi

echo ""
echo "诊断完成！"