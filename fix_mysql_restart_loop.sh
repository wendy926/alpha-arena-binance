#!/bin/bash

echo "🔧 修复MySQL重启循环问题"
echo "========================="

echo "步骤1: 停止所有服务..."
docker-compose down

echo ""
echo "步骤2: 检查磁盘空间..."
df -h .

echo ""
echo "步骤3: 备份并重置MySQL数据目录..."
if [ -d "./mysql-data" ]; then
    echo "备份现有数据目录..."
    mv ./mysql-data ./mysql-data-backup-$(date +%Y%m%d-%H%M%S) 2>/dev/null || sudo mv ./mysql-data ./mysql-data-backup-$(date +%Y%m%d-%H%M%S)
fi

echo "创建新的MySQL数据目录..."
mkdir -p ./mysql-data

echo ""
echo "步骤4: 设置正确的权限..."
# MySQL容器使用uid:gid = 999:999
chown -R 999:999 ./mysql-data 2>/dev/null || sudo chown -R 999:999 ./mysql-data
chmod -R 755 ./mysql-data

echo "权限设置完成:"
ls -la ./mysql-data

echo ""
echo "步骤5: 清理Docker缓存..."
docker system prune -f

echo ""
echo "步骤6: 启动MySQL容器（仅MySQL）..."
docker-compose up -d mysql

echo ""
echo "步骤7: 监控MySQL启动过程（60秒）..."
for i in {1..12}; do
    echo "检查第 $i 次 ($(($i * 5))秒)..."
    
    # 检查容器状态
    status=$(docker-compose ps mysql --format "table {{.Status}}" | tail -n 1)
    echo "容器状态: $status"
    
    # 检查是否包含 "Up" 状态
    if echo "$status" | grep -q "Up"; then
        echo "✅ MySQL容器启动成功！"
        break
    fi
    
    # 如果是最后一次检查，显示详细日志
    if [ $i -eq 12 ]; then
        echo "❌ MySQL启动失败，显示详细日志:"
        docker-compose logs mysql | tail -30
        
        echo ""
        echo "💡 可能的解决方案:"
        echo "1. 检查磁盘空间是否充足"
        echo "2. 检查SELinux设置: sestatus"
        echo "3. 尝试使用不同的MySQL版本"
        echo "4. 检查Docker版本兼容性"
        exit 1
    fi
    
    sleep 5
done

echo ""
echo "步骤8: 测试MySQL连接..."
sleep 10
if docker-compose exec mysql mysqladmin ping -h localhost 2>/dev/null; then
    echo "✅ MySQL连接测试成功！"
    
    echo ""
    echo "步骤9: 启动完整服务..."
    docker-compose up -d
    
    echo ""
    echo "🎉 所有服务状态:"
    docker-compose ps
    
    echo ""
    echo "✅ MySQL修复完成！现在可以运行数据恢复:"
    echo "python3 restore_data_docker.py"
    
else
    echo "❌ MySQL连接仍然失败"
    echo "显示MySQL日志:"
    docker-compose logs mysql | tail -20
fi