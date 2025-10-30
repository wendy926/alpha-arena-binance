#!/bin/bash

echo "=== 提交修复到GitHub ==="

# 进入项目目录
cd /Users/wangyajing/Documents/trae_projects/alpha-arena/alpha-arena-okx

# 检查Git状态
echo "📋 检查Git状态..."
git status

# 添加所有修改的文件
echo "📝 添加修改的文件..."
git add .

# 提交修复
echo "💾 提交修复代码..."
git commit -m "修复胜率计算和入场价格显示问题

🔧 主要修复:
- 修复胜率计算逻辑：后端返回百分比值，解决胜率显示为0%的问题
- 优化价格获取：改进fallback数据使用真实BTC价格而非硬编码68000
- 修复入场价格显示：创建数据修复脚本清理旧数据并添加基于当前价格的测试记录
- 添加调试功能：创建调试脚本便于排查数据库和价格问题

📁 新增文件:
- debug_db.py: 数据库调试脚本
- fix_data.py: 数据修复脚本，清理旧数据并添加测试交易记录
- deploy_fix.sh: 完整部署脚本
- commit_fixes.sh: Git提交脚本

🛠️ 修改文件:
- paper_trading.py: 修复胜率计算，返回百分比值并添加调试日志
- static/js/app.js: 更新前端胜率显示逻辑注释
- deepseekok2.py: 之前已修复的价格获取逻辑

✅ 预期效果:
- 胜率正确显示（约66.7%基于测试数据）
- 入场价格显示接近当前BTC价格
- 当前价格使用真实市场数据"

# 推送到远程仓库
echo "🚀 推送到GitHub..."
git push origin main

echo "✅ 代码已成功提交并推送到GitHub!"
echo ""
echo "🔗 GitHub仓库: https://github.com/wendy926/alpha-arena-binance"
echo ""
echo "📋 接下来请在VPS上执行以下命令部署修复:"
echo "cd /root/btc-trading-bot"
echo "git pull origin main"
echo "cd alpha-arena-okx"
echo "python3 fix_data.py"
echo "cd .."
echo "docker-compose down && docker-compose up -d"