#!/bin/bash

# 设置颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "  BTC交易机器人 - SQLite Docker启动脚本"
echo "========================================"
echo ""

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}[错误]${NC} Docker未运行或未安装！"
    echo ""
    echo "请先启动Docker服务"
    echo "Ubuntu/Debian: sudo systemctl start docker"
    echo "macOS: 启动Docker Desktop"
    echo ""
    exit 1
fi

echo -e "${GREEN}[✓]${NC} Docker运行正常"
echo ""

# 检查.env文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[警告]${NC} 未找到.env配置文件！"
    echo ""
    echo "请先创建.env文件并配置API密钥"
    echo "参考.env.example文件"
    echo ""
    exit 1
fi

echo -e "${GREEN}[✓]${NC} 配置文件已找到"
echo ""

# 检查docker-compose-sqlite.yml
if [ ! -f "docker-compose-sqlite.yml" ]; then
    echo -e "${RED}[错误]${NC} 未找到docker-compose-sqlite.yml文件！"
    exit 1
fi

echo "[启动] 正在启动SQLite版本Docker容器..."
echo ""

# 停止可能存在的旧容器
echo "🛑 停止旧容器..."
docker-compose -f docker-compose-sqlite.yml down

# 创建数据目录
echo "📁 创建数据目录..."
mkdir -p data

# 启动容器
echo "🚀 启动新容器..."
docker-compose -f docker-compose-sqlite.yml up -d

# 检查启动状态
echo ""
echo "⏳ 等待容器启动..."
sleep 10

# 检查容器状态
if docker ps | grep -q "btc-trading-bot-sqlite"; then
    echo -e "${GREEN}[✓]${NC} 容器启动成功！"
    echo ""
    echo "🌐 访问地址: http://localhost:8080"
    echo "📊 API文档: http://localhost:8080/api/dashboard"
    echo ""
    echo "📋 查看日志: docker logs btc-trading-bot-sqlite -f"
    echo "🛑 停止服务: docker-compose -f docker-compose-sqlite.yml down"
    echo ""
else
    echo -e "${RED}[错误]${NC} 容器启动失败！"
    echo ""
    echo "查看错误日志:"
    docker logs btc-trading-bot-sqlite
    exit 1
fi