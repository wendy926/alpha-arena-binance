#!/bin/bash
# 手动修复命令 - 在VPS上逐步执行

echo "🔧 手动修复步骤 - 请在VPS上逐步执行以下命令"
echo "=================================================="

echo ""
echo "1️⃣ 查找并终止占用端口的进程："
echo "lsof -ti:8080 | xargs kill -9"
echo "pkill -f web_server.py"
echo "pkill -f deepseekok2.py"

echo ""
echo "2️⃣ 等待进程完全退出："
echo "sleep 5"

echo ""
echo "3️⃣ 检查端口是否释放："
echo "lsof -i:8080"
echo "# 如果没有输出，说明端口已释放"

echo ""
echo "4️⃣ 启动web服务器："
echo "nohup python3 web_server.py > web_server.log 2>&1 &"

echo ""
echo "5️⃣ 检查服务是否启动："
echo "sleep 3"
echo "ps aux | grep web_server"

echo ""
echo "6️⃣ 测试API："
echo "curl -s http://localhost:8080/api/dashboard | head -100"

echo ""
echo "7️⃣ 检查网站："
echo "访问: https://arena.aimaventop.com/flow/"

echo ""
echo "8️⃣ 如果问题仍然存在，检查日志："
echo "tail -20 web_server.log"

echo ""
echo "=================================================="
echo "💡 提示：如果端口仍被占用，可以尝试重启整个VPS"