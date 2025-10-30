#!/bin/bash

echo "🔍 检查MySQL状态详情"
echo "==================="

echo "步骤1: 检查所有Docker容器状态..."
docker-compose ps

echo ""
echo "步骤2: 检查MySQL容器详细信息..."
docker ps | grep mysql

echo ""
echo "步骤3: 检查MySQL容器日志（最后20行）..."
docker-compose logs mysql | tail -20

echo ""
echo "步骤4: 检查端口3306占用情况..."
netstat -tlnp | grep 3306 || echo "端口3306未被占用"

echo ""
echo "步骤5: 尝试从容器内部连接MySQL..."
if docker-compose exec mysql mysqladmin ping -h localhost 2>/dev/null; then
    echo "✅ 容器内部MySQL连接成功"
else
    echo "❌ 容器内部MySQL连接失败"
fi

echo ""
echo "步骤6: 检查MySQL容器网络配置..."
docker-compose exec mysql cat /etc/hosts | grep mysql || echo "无法读取容器hosts文件"

echo ""
echo "步骤7: 尝试不同的连接方式..."
echo "测试localhost连接:"
docker-compose exec mysql mysql -h localhost -u root -proot123 -e "SELECT 1;" 2>/dev/null && echo "✅ localhost连接成功" || echo "❌ localhost连接失败"

echo "测试127.0.0.1连接:"
docker-compose exec mysql mysql -h 127.0.0.1 -u root -proot123 -e "SELECT 1;" 2>/dev/null && echo "✅ 127.0.0.1连接成功" || echo "❌ 127.0.0.1连接失败"

echo ""
echo "步骤8: 检查MySQL进程..."
docker-compose exec mysql ps aux | grep mysql || echo "无法检查MySQL进程"

echo ""
echo "步骤9: 检查MySQL配置文件..."
docker-compose exec mysql cat /etc/mysql/my.cnf | grep bind-address || echo "未找到bind-address配置"