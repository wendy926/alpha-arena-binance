#!/bin/bash
# 快速Docker修复脚本
# 解决常见的Docker构建问题

echo "🚀 快速Docker修复开始..."
echo "时间: $(date)"
echo "=================================================="

# 1. 检查基本文件
echo "📁 检查基本文件..."
for file in Dockerfile docker-compose.yml requirements.txt; do
    if [ -f "$file" ]; then
        echo "✅ $file 存在"
    else
        echo "❌ $file 不存在"
    fi
done

# 2. 检查.env文件
if [ ! -f ".env" ]; then
    echo "❌ .env文件不存在"
    if [ -f ".env_template" ]; then
        echo "💡 复制.env_template为.env..."
        cp .env_template .env
        echo "✅ 已创建.env文件"
    else
        echo "⚠️ 需要手动创建.env文件"
    fi
fi

# 3. 清理Docker缓存
echo "🧹 清理Docker缓存..."
docker system prune -f
docker builder prune -f

# 4. 停止并删除现有容器
echo "🛑 停止并删除现有容器..."
docker-compose down --volumes --remove-orphans

# 5. 删除相关镜像
echo "🗑️ 删除相关镜像..."
docker rmi $(docker images | grep alpha-arena | awk '{print $3}') 2>/dev/null || true

# 6. 检查网络连接
echo "🌐 检查网络连接..."
if ping -c 1 pypi.tuna.tsinghua.edu.cn > /dev/null 2>&1; then
    echo "✅ 网络连接正常"
else
    echo "❌ 网络连接有问题"
fi

# 7. 检查磁盘空间
echo "💾 检查磁盘空间..."
df -h .

# 8. 尝试构建（分步骤）
echo "🔨 尝试分步骤构建..."

# 8.1 先测试基础镜像
echo "测试基础镜像..."
docker pull python:3.11-slim

# 8.2 创建简化的Dockerfile
echo "创建简化Dockerfile..."
cat > Dockerfile.simple << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 先安装基础包
RUN pip install --no-cache-dir flask requests python-dotenv pandas

# 复制requirements.txt并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制应用文件
COPY . .

EXPOSE 8080

CMD ["python", "web_server.py"]
EOF

# 8.3 尝试简化构建
echo "尝试简化构建..."
if docker build -f Dockerfile.simple -t alpha-arena-simple . --no-cache; then
    echo "✅ 简化构建成功！"
    
    # 8.4 更新docker-compose.yml使用简化镜像
    echo "更新docker-compose.yml..."
    sed -i.bak 's/build:/# build:/' docker-compose.yml
    sed -i.bak 's/context: ./# context: ./' docker-compose.yml
    sed -i.bak 's/dockerfile: Dockerfile/# dockerfile: Dockerfile/' docker-compose.yml
    sed -i.bak '/container_name: btc-trading-bot/i\    image: alpha-arena-simple' docker-compose.yml
    
    echo "✅ 已更新docker-compose.yml使用简化镜像"
else
    echo "❌ 简化构建也失败了"
    
    # 9. 显示详细错误信息
    echo "📋 显示详细构建日志..."
    docker build -f Dockerfile.simple -t alpha-arena-simple . --no-cache --progress=plain
fi

# 10. 尝试启动服务
echo "🚀 尝试启动服务..."
if docker-compose up -d; then
    echo "✅ 服务启动成功！"
    
    # 等待服务启动
    echo "⏳ 等待服务启动..."
    sleep 30
    
    # 检查服务状态
    echo "🏥 检查服务状态..."
    docker-compose ps
    
    # 测试API
    echo "🔗 测试API..."
    curl -s http://localhost:8080/api/dashboard | python3 -m json.tool || echo "API测试失败"
    
else
    echo "❌ 服务启动失败"
    echo "📋 查看日志..."
    docker-compose logs
fi

echo "=================================================="
echo "✅ 快速修复完成！"
echo ""
echo "如果仍有问题，请运行: python3 debug_docker_build.py"