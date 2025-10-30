#!/bin/bash
# 快速端口清理脚本

echo "🔧 快速清理端口占用..."

# 1. 检查端口占用情况
echo "============================================================"
echo "📋 检查端口占用情况..."

echo "端口8080占用情况："
lsof -i :8080 || echo "端口8080未被占用"

echo "端口8081占用情况："
lsof -i :8081 || echo "端口8081未被占用"

echo "端口8089占用情况："
lsof -i :8089 || echo "端口8089未被占用"

# 2. 停止相关进程
echo "============================================================"
echo "🛑 停止相关进程..."

# 停止web_server.py进程
echo "停止web_server.py进程..."
pkill -f "web_server.py" 2>/dev/null || true

# 停止deepseekok2.py进程
echo "停止deepseekok2.py进程..."
pkill -f "deepseekok2.py" 2>/dev/null || true

# 停止python3进程（谨慎）
echo "停止可能的python3 web服务进程..."
ps aux | grep "python3.*web_server" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

# 3. 强制清理端口
echo "============================================================"
echo "🧹 强制清理端口..."

# 清理8080端口
echo "清理端口8080..."
lsof -ti:8080 | xargs kill -9 2>/dev/null || true

# 清理8081端口
echo "清理端口8081..."
lsof -ti:8081 | xargs kill -9 2>/dev/null || true

# 清理8089端口
echo "清理端口8089..."
lsof -ti:8089 | xargs kill -9 2>/dev/null || true

# 4. 等待端口释放
echo "============================================================"
echo "⏳ 等待端口释放..."
sleep 3

# 5. 再次检查端口状态
echo "============================================================"
echo "✅ 检查端口清理结果..."

echo "端口8080状态："
if lsof -i :8080 >/dev/null 2>&1; then
    echo "❌ 端口8080仍被占用"
    lsof -i :8080
else
    echo "✅ 端口8080已释放"
fi

echo "端口8081状态："
if lsof -i :8081 >/dev/null 2>&1; then
    echo "❌ 端口8081仍被占用"
    lsof -i :8081
else
    echo "✅ 端口8081已释放"
fi

echo "端口8089状态："
if lsof -i :8089 >/dev/null 2>&1; then
    echo "❌ 端口8089仍被占用"
    lsof -i :8089
else
    echo "✅ 端口8089已释放"
fi

# 6. 建议下一步操作
echo "============================================================"
echo "🚀 建议的启动命令："
echo ""
echo "选项1 - 使用端口8081："
echo "PORT=8081 python3 web_server.py"
echo ""
echo "选项2 - 使用端口8089："
echo "PORT=8089 python3 web_server.py"
echo ""
echo "选项3 - 使用端口8082："
echo "PORT=8082 python3 web_server.py"
echo ""
echo "🌐 访问地址将是："
echo "http://your-server-ip:PORT"
echo "============================================================"