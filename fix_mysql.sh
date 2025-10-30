#!/bin/bash

echo "🔍 MySQL容器启动问题诊断和修复脚本"
echo "=================================="

# 1. 检查磁盘空间
echo "1. 检查磁盘空间..."
df -h

echo ""
echo "2. 检查Docker状态..."
docker --version
docker-compose --version

echo ""
echo "3. 停止所有容器..."
docker-compose down

echo ""
echo "4. 检查MySQL数据目录..."
if [ -d "./mysql-data" ]; then
    echo "MySQL数据目录存在，检查权限..."
    ls -la ./mysql-data
    echo "数据目录大小:"
    du -sh ./mysql-data
else
    echo "MySQL数据目录不存在，将创建..."
    mkdir -p ./mysql-data
fi

echo ""
echo "5. 修复MySQL数据目录权限..."
# MySQL容器内的mysql用户UID通常是999
sudo chown -R 999:999 ./mysql-data
sudo chmod -R 755 ./mysql-data

echo ""
echo "6. 检查端口占用..."
netstat -tlnp | grep :3306 || echo "端口3306未被占用"

echo ""
echo "7. 清理可能损坏的MySQL数据..."
read -p "是否要清理MySQL数据目录重新初始化？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "备份现有数据..."
    if [ -d "./mysql-data" ]; then
        mv ./mysql-data ./mysql-data-backup-$(date +%Y%m%d_%H%M%S)
    fi
    mkdir -p ./mysql-data
    sudo chown -R 999:999 ./mysql-data
    sudo chmod -R 755 ./mysql-data
    echo "MySQL数据目录已重置"
fi

echo ""
echo "8. 移除obsolete version警告..."
# 创建临时文件，移除version行
grep -v "^version:" docker-compose.yml > docker-compose-temp.yml
mv docker-compose-temp.yml docker-compose.yml

echo ""
echo "9. 尝试启动MySQL容器..."
docker-compose up -d mysql

echo ""
echo "10. 等待MySQL启动..."
sleep 30

echo ""
echo "11. 检查MySQL容器状态..."
docker-compose ps
docker-compose logs mysql

echo ""
echo "12. 如果MySQL启动成功，启动完整服务..."
if docker-compose ps mysql | grep -q "Up"; then
    echo "✅ MySQL启动成功，启动完整服务..."
    docker-compose up -d
    echo ""
    echo "🎉 服务启动完成！"
    echo "检查服务状态:"
    docker-compose ps
else
    echo "❌ MySQL启动失败，查看详细日志:"
    docker-compose logs mysql
fi

echo ""
echo "修复脚本执行完成！"