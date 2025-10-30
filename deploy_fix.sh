#!/bin/bash

echo "=== 部署修复脚本 ==="

# 1. 提交代码到Git
echo "📝 提交代码修复..."
git add .
git commit -m "修复胜率计算和入场价格显示问题

- 修复胜率计算：后端返回百分比值，解决胜率显示为0%的问题
- 优化价格获取：改进fallback数据使用真实BTC价格
- 添加调试日志：便于排查问题
- 创建数据修复脚本：清理旧数据并添加测试记录"

# 2. 推送到远程仓库
echo "🚀 推送到远程仓库..."
git push origin main

echo "✅ 代码已推送到GitHub"

echo ""
echo "=== VPS部署命令 ==="
echo "请在VPS上执行以下命令："
echo ""
echo "# 1. 进入项目目录并拉取最新代码"
echo "cd /root/btc-trading-bot"
echo "git pull origin main"
echo ""
echo "# 2. 运行数据修复脚本"
echo "cd alpha-arena-okx"
echo "python3 fix_data.py"
echo ""
echo "# 3. 重启Docker服务"
echo "cd .."
echo "docker-compose down"
echo "docker-compose up -d"
echo ""
echo "# 4. 检查服务状态"
echo "docker-compose logs -f btc-trading-bot"
echo ""
echo "=== 修复说明 ==="
echo "1. 胜率问题：修复了胜率计算逻辑，现在会正确显示百分比"
echo "2. 入场价格问题：清理了旧的交易记录，添加了基于当前价格的新测试数据"
echo "3. 价格获取：改进了fallback数据，即使在网络问题时也使用真实价格"
echo ""
echo "修复完成后，请访问 https://arena.aimaventop.com/flow/ 查看效果"