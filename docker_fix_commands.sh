#!/bin/bash
# Docker架构VPS修复命令
# 针对完整的Docker Compose服务架构

echo "🚀 Docker架构VPS修复开始..."
echo "时间: $(date)"
echo "=================================================="

# 1. 检查Docker环境
echo "🐳 检查Docker环境..."
docker --version
docker-compose --version

# 2. 查看当前运行的容器
echo "📋 当前运行的容器:"
docker ps

# 3. 停止所有Docker服务
echo "🛑 停止Docker服务..."
docker-compose down --volumes --remove-orphans

# 4. 清理端口占用
echo "🧹 清理端口占用..."
# 杀死占用8080端口的进程
lsof -ti:8080 | xargs -r kill -9
# 杀死占用3306端口的进程  
lsof -ti:3306 | xargs -r kill -9

# 等待清理完成
echo "⏳ 等待清理完成..."
sleep 5

# 5. 备份关键文件
echo "📁 备份关键文件..."
if [ -f "paper_trading.py" ]; then
    cp paper_trading.py "paper_trading_backup_$(date +%s).py"
    echo "✅ 已备份 paper_trading.py"
fi

# 6. 修复paper_trading.py中的胜率计算问题
echo "🔧 修复胜率计算问题..."
cat > fix_winrate.py << 'EOF'
import re

# 修复后的函数代码
fix_code = '''def compute_win_rate_from_db():
    """从数据库计算胜率和盈亏"""
    try:
        trades = get_all_trades()
        if not trades:
            return {
                'win_rate': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'total_profit': 0.0,
                'avg_profit_per_trade': 0.0
            }
        
        total_trades = len(trades)
        winning_trades = 0
        total_profit = 0.0
        
        for trade in trades:
            # 跳过无效的交易记录
            if not trade.get('price') or not trade.get('amount'):
                continue
            if trade.get('price') == 0 or trade.get('amount') == 0:
                continue
                
            profit = float(trade.get('profit', 0))
            total_profit += profit
            
            if profit > 0:
                winning_trades += 1
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
        avg_profit = total_profit / total_trades if total_trades > 0 else 0.0
        
        return {
            'win_rate': round(win_rate, 2),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'total_profit': round(total_profit, 2),
            'avg_profit_per_trade': round(avg_profit, 2)
        }
        
    except Exception as e:
        print(f"计算胜率时出错: {e}")
        return {
            'win_rate': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'total_profit': 0.0,
            'avg_profit_per_trade': 0.0
        }'''

# 读取文件
with open("paper_trading.py", "r", encoding="utf-8") as f:
    content = f.read()

# 替换函数
pattern = r'def compute_win_rate_from_db\(\):.*?(?=\ndef|\nclass|\n[a-zA-Z_]|\Z)'
if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, fix_code, content, flags=re.DOTALL)
    
    with open("paper_trading.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ 已修复 paper_trading.py")
else:
    print("⚠️ 未找到函数，跳过修复")
EOF

python3 fix_winrate.py
rm fix_winrate.py

# 7. 重新构建Docker镜像
echo "🔨 重新构建Docker镜像..."
docker-compose build --no-cache

# 8. 启动Docker服务
echo "🚀 启动Docker服务..."
docker-compose up -d

# 9. 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 10. 检查服务状态
echo "🏥 检查服务状态..."
echo "容器状态:"
docker-compose ps

echo "端口监听状态:"
netstat -tlnp | grep :8080
netstat -tlnp | grep :3306

# 11. 测试API
echo "🔗 测试API..."
curl -s http://localhost:8080/api/dashboard | python3 -m json.tool

# 12. 检查容器日志
echo "📋 检查容器日志..."
echo "=== btc-trading-bot 日志 ==="
docker-compose logs --tail=20 btc-trading-bot

echo "=== MySQL 日志 ==="
docker-compose logs --tail=10 mysql

echo "=================================================="
echo "✅ Docker修复完成！"
echo "🌐 网站地址: http://your-vps-ip:8080"
echo "📊 API测试: http://your-vps-ip:8080/api/dashboard"
echo ""
echo "如果问题仍然存在，请检查:"
echo "1. .env文件配置是否正确"
echo "2. DEEPSEEK_API_KEY是否有效"
echo "3. 容器日志是否有错误信息"