#!/bin/bash

echo "🚀 MySQL容器快速修复脚本"
echo "========================"

# 停止所有服务
echo "1. 停止Docker服务..."
docker-compose down

# 移除version警告
echo "2. 修复docker-compose.yml..."
sed -i '/^version:/d' docker-compose.yml

# 检查并创建MySQL数据目录
echo "3. 检查MySQL数据目录..."
if [ ! -d "./mysql-data" ]; then
    mkdir -p ./mysql-data
fi

# 修复权限（MySQL容器内mysql用户UID是999）
echo "4. 修复MySQL数据目录权限..."
chown -R 999:999 ./mysql-data 2>/dev/null || sudo chown -R 999:999 ./mysql-data
chmod -R 755 ./mysql-data

# 清理可能的端口占用
echo "5. 检查端口占用..."
if netstat -tlnp | grep -q :3306; then
    echo "警告: 端口3306被占用，尝试清理..."
    pkill -f mysql 2>/dev/null || true
fi

# 清理Docker缓存
echo "6. 清理Docker缓存..."
docker system prune -f

# 重新启动服务
echo "7. 启动MySQL服务..."
docker-compose up -d mysql

# 等待MySQL启动
echo "8. 等待MySQL启动（30秒）..."
sleep 30

# 检查MySQL状态
echo "9. 检查MySQL状态..."
if docker-compose ps mysql | grep -q "Up"; then
    echo "✅ MySQL启动成功！"
    echo "10. 启动完整服务..."
    docker-compose up -d
    echo ""
    echo "🎉 所有服务启动完成！"
    docker-compose ps
else
    echo "❌ MySQL仍然启动失败，显示详细日志:"
    docker-compose logs mysql | tail -20
    echo ""
    echo "💡 建议手动操作:"
    echo "1. 检查磁盘空间: df -h"
    echo "2. 重置MySQL数据: rm -rf ./mysql-data && mkdir ./mysql-data"
    echo "3. 重新运行此脚本"
fi