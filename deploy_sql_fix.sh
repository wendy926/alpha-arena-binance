#!/bin/bash

echo "🔧 部署SQL语法修复"
echo "==================="

# VPS信息
VPS_IP="47.236.15.204"
VPS_USER="root"
VPS_PATH="/opt/alpha-arena/alpha-arena-binance"

echo "📤 上传修复后的paper_trading.py..."
scp paper_trading.py ${VPS_USER}@${VPS_IP}:${VPS_PATH}/

echo "🔄 重启应用容器..."
ssh ${VPS_USER}@${VPS_IP} "cd ${VPS_PATH} && docker-compose restart btc-trading-bot"

echo "⏳ 等待容器启动..."
sleep 10

echo "🧪 测试修复结果..."
ssh ${VPS_USER}@${VPS_IP} "curl -s http://localhost:8080/api/dashboard | jq '.performance'"

echo "📋 检查应用日志..."
ssh ${VPS_USER}@${VPS_IP} "docker logs btc-trading-bot --tail 10 | grep -E '(计算纸上持仓|SQL|error)'"

echo "✅ SQL语法修复部署完成！"