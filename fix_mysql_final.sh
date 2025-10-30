#!/bin/bash

echo "🔧 MySQL最终修复方案"
echo "==================="

echo "步骤1: 检查系统资源..."
echo "磁盘空间:"
df -h .
echo ""
echo "内存使用:"
free -h
echo ""
echo "Docker版本:"
docker --version

echo ""
echo "步骤2: 完全停止并清理Docker..."
docker-compose down
docker system prune -f
docker volume prune -f

echo ""
echo "步骤3: 彻底清理MySQL数据目录..."
if [ -d "./mysql-data" ]; then
    echo "删除现有MySQL数据目录..."
    rm -rf ./mysql-data 2>/dev/null || sudo rm -rf ./mysql-data
fi

echo "创建新的MySQL数据目录..."
mkdir -p ./mysql-data
chown -R 999:999 ./mysql-data 2>/dev/null || sudo chown -R 999:999 ./mysql-data
chmod -R 755 ./mysql-data

echo ""
echo "步骤4: 检查docker-compose.yml中的MySQL配置..."
echo "当前MySQL配置:"
grep -A 20 "mysql:" docker-compose.yml

echo ""
echo "步骤5: 尝试使用MySQL 5.7（更稳定的版本）..."
# 备份原始docker-compose.yml
cp docker-compose.yml docker-compose.yml.backup

# 替换MySQL版本为5.7
sed -i 's/mysql:8.0/mysql:5.7/g' docker-compose.yml

echo "已将MySQL版本从8.0改为5.7"

echo ""
echo "步骤6: 添加MySQL内存限制配置..."
# 检查是否已有内存限制配置
if ! grep -q "mem_limit" docker-compose.yml; then
    echo "添加内存限制配置..."
    # 这里我们手动提示用户添加配置，因为sed操作可能比较复杂
    echo "⚠️  请手动在docker-compose.yml的mysql服务中添加以下配置:"
    echo "    mem_limit: 512m"
    echo "    environment:"
    echo "      - MYSQL_INNODB_BUFFER_POOL_SIZE=128M"
fi

echo ""
echo "步骤7: 启动MySQL 5.7容器..."
docker-compose up -d mysql

echo ""
echo "步骤8: 监控MySQL 5.7启动过程（90秒）..."
for i in {1..18}; do
    echo "检查第 $i 次 ($(($i * 5))秒)..."
    
    # 检查容器状态
    status=$(docker-compose ps mysql --format "table {{.Status}}" | tail -n 1)
    echo "容器状态: $status"
    
    # 检查是否包含 "Up" 状态且不是重启状态
    if echo "$status" | grep -q "Up" && ! echo "$status" | grep -q "Restarting"; then
        echo "✅ MySQL 5.7容器启动成功！"
        
        # 等待额外10秒确保MySQL完全启动
        echo "等待MySQL完全启动..."
        sleep 10
        
        # 测试连接
        if docker-compose exec mysql mysqladmin ping -h localhost --silent 2>/dev/null; then
            echo "✅ MySQL连接测试成功！"
            break
        else
            echo "⚠️  容器运行但连接失败，继续等待..."
        fi
    fi
    
    # 如果是重启状态，显示日志
    if echo "$status" | grep -q "Restarting"; then
        echo "❌ MySQL仍在重启，显示日志:"
        docker-compose logs mysql | tail -10
    fi
    
    # 如果是最后一次检查
    if [ $i -eq 18 ]; then
        echo "❌ MySQL 5.7启动失败"
        echo "显示完整日志:"
        docker-compose logs mysql
        
        echo ""
        echo "💡 尝试恢复MySQL 8.0配置..."
        cp docker-compose.yml.backup docker-compose.yml
        echo "已恢复原始配置"
        
        echo ""
        echo "🆘 建议的最后解决方案:"
        echo "1. 检查VPS内存是否足够（建议至少1GB）"
        echo "2. 检查磁盘空间是否充足"
        echo "3. 考虑使用SQLite替代MySQL"
        echo "4. 联系VPS提供商检查系统兼容性"
        exit 1
    fi
    
    sleep 5
done

echo ""
echo "步骤9: 启动完整服务..."
docker-compose up -d

echo ""
echo "步骤10: 检查所有服务状态..."
docker-compose ps

echo ""
echo "🎉 MySQL 5.7修复完成！现在可以运行数据恢复:"
echo "python3 restore_data_docker.py"