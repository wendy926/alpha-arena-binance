#!/bin/bash

echo "🔧 手动MySQL修复步骤"
echo "==================="

# 检查当前状态
echo "步骤1: 检查当前Docker状态..."
docker-compose ps

echo ""
echo "步骤2: 检查MySQL数据目录..."
if [ -d "./mysql-data" ]; then
    echo "MySQL数据目录存在，检查权限..."
    ls -la ./mysql-data
else
    echo "创建MySQL数据目录..."
    mkdir -p ./mysql-data
fi

echo ""
echo "步骤3: 修复MySQL数据目录权限..."
chown -R 999:999 ./mysql-data 2>/dev/null || sudo chown -R 999:999 ./mysql-data
chmod -R 755 ./mysql-data
echo "权限修复完成"

echo ""
echo "步骤4: 启动MySQL容器..."
docker-compose up -d mysql

echo ""
echo "步骤5: 等待MySQL启动（30秒）..."
sleep 30

echo ""
echo "步骤6: 检查MySQL容器状态..."
docker-compose ps mysql

echo ""
echo "步骤7: 检查MySQL日志..."
docker-compose logs mysql | tail -10

echo ""
echo "步骤8: 测试MySQL连接..."
if docker-compose exec mysql mysqladmin ping -h localhost 2>/dev/null; then
    echo "✅ MySQL连接成功！"
    
    echo ""
    echo "步骤9: 启动完整服务..."
    docker-compose up -d
    
    echo ""
    echo "🎉 所有服务状态:"
    docker-compose ps
    
    echo ""
    echo "✅ MySQL修复完成！现在可以运行数据恢复脚本:"
    echo "python3 restore_data_py36.py"
    
else
    echo "❌ MySQL连接失败，显示详细日志:"
    docker-compose logs mysql
    
    echo ""
    echo "💡 建议重置MySQL数据目录:"
    echo "sudo rm -rf ./mysql-data"
    echo "mkdir -p ./mysql-data"
    echo "sudo chown -R 999:999 ./mysql-data"
    echo "docker-compose up -d mysql"
fi