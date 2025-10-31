#!/bin/bash
# 最终修复解决方案 - 解决生产环境盈亏为0问题

echo "🔧 Alpha Arena 最终修复解决方案"
echo "=================================="

# 1. 确认本地修复代码
echo "1. 检查本地修复代码..."
if grep -q "跳过无效记录" paper_trading.py; then
    echo "   ✅ 本地paper_trading.py包含修复代码"
else
    echo "   ❌ 本地paper_trading.py缺少修复代码"
    echo "   请先运行: python3 fix_profit_calculation.py"
    exit 1
fi

# 2. 同步到VPS (需要手动执行)
echo ""
echo "2. 同步修复代码到VPS..."
echo "   请手动执行以下命令将修复后的文件上传到VPS："
echo "   scp paper_trading.py user@your-vps:/path/to/alpha-arena/"
echo ""

# 3. VPS上的操作指令
echo "3. 在VPS上执行以下命令："
echo "   # 检查修复代码是否存在"
echo "   grep -n '跳过无效记录' paper_trading.py"
echo ""
echo "   # 停止现有进程"
echo "   pkill -f web_server.py"
echo "   pkill -f deepseekok2.py"
echo ""
echo "   # 重启服务"
echo "   nohup python3 web_server.py > web_server.log 2>&1 &"
echo ""
echo "   # 验证服务状态"
echo "   curl http://localhost:8080/api/dashboard"
echo ""

# 4. 验证修复
echo "4. 验证修复结果："
echo "   访问: https://arena.aimaventop.com/flow/"
echo "   检查胜率和盈亏数据是否正常显示"
echo ""

# 5. 备用方案
echo "5. 如果问题仍然存在："
echo "   - 检查VPS数据库连接配置"
echo "   - 清理浏览器缓存"
echo "   - 检查VPS防火墙和端口设置"
echo "   - 查看VPS日志: tail -f web_server.log"
echo ""

echo "=================================="
echo "✅ 修复方案准备完成"
echo "请按照上述步骤手动执行VPS操作"