#!/bin/bash

# Alpha Arena v1.0.0 发布脚本
# 用于提交变更、推送到GitHub并创建v1.0.0标签

echo "🚀 开始发布 Alpha Arena v1.0.0..."

# 检查Git状态
echo "📋 检查Git状态..."
git status

# 添加所有变更
echo "📦 添加所有变更到暂存区..."
git add .

# 提交变更
echo "💾 提交变更..."
git commit -m "feat: 发布v1.0.0版本

✨ 新功能:
- 基于DeepSeek AI的智能交易决策系统
- 完整的Web监控界面
- SQLite数据库支持
- Docker容器化部署
- 模拟交易功能

🔧 技术特性:
- AI驱动的市场分析
- 技术指标综合分析
- 实时数据可视化
- 风险管理系统

📁 项目结构优化:
- 删除冗余文件和临时脚本
- 整理核心业务逻辑代码
- 更新项目文档
- 简化部署流程

🐳 部署支持:
- Docker Compose配置
- 环境变量模板
- 启动脚本

📚 文档完善:
- 更新README.md
- 配置说明
- 快速开始指南
- 故障排除指南"

# 推送到GitHub
echo "🌐 推送到GitHub..."
git push origin main

# 创建v1.0.0标签
echo "🏷️ 创建v1.0.0标签..."
git tag -a v1.0.0 -m "Alpha Arena v1.0.0 正式版本

🎉 首个正式版本发布！

核心功能:
✅ DeepSeek AI智能交易决策
✅ Web监控界面
✅ SQLite数据库
✅ Docker部署
✅ 模拟交易
✅ 技术指标分析
✅ 风险管理

技术栈:
- Python 3.8+
- Flask Web框架
- SQLite数据库
- Docker容器化
- ECharts图表
- Bootstrap UI

部署方式:
- 本地Python运行
- Docker Compose部署
- VPS云服务器部署

⚠️ 注意: 本版本为学习研究用途，实际交易请谨慎使用。"

# 推送标签
echo "📤 推送标签到GitHub..."
git push origin v1.0.0

echo "✅ Alpha Arena v1.0.0 发布完成！"
echo ""
echo "🔗 GitHub仓库: https://github.com/your-username/alpha-arena-okx"
echo "🏷️ 版本标签: v1.0.0"
echo "📖 查看发布: https://github.com/your-username/alpha-arena-okx/releases/tag/v1.0.0"
echo ""
echo "🎉 恭喜！您的AI交易机器人项目已成功发布！"