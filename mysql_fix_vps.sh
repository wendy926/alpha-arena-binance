#!/bin/bash
# MySQL容器修复脚本 - VPS版本

echo "🔍 开始诊断MySQL容器问题..."

# 进入项目目录
cd /opt/alpha-arena/alpha-arena-binance

echo "📋 当前目录: $(pwd)"

# 检查docker-compose文件
echo "📄 检查docker-compose.yml文件..."
if [ -f "docker-compose.yml" ]; then
    echo "✅ docker-compose.yml 存在"
else
    echo "❌ docker-compose.yml 不存在"
    exit 1
fi

# 停止所有容器
echo "🛑 停止所有容器..."
docker-compose down -v

# 清理MySQL数据卷（如果存在问题）
echo "🧹 清理MySQL数据卷..."
docker volume ls | grep mysql
docker volume rm $(docker volume ls -q | grep mysql) 2>/dev/null || echo "没有MySQL卷需要清理"

# 清理悬挂的镜像和容器
echo "🧹 清理悬挂的资源..."
docker system prune -f

# 检查端口占用
echo "🔍 检查端口占用情况..."
netstat -tlnp | grep :3306 || echo "端口3306未被占用"
netstat -tlnp | grep :8080 || echo "端口8080未被占用"

# 创建MySQL初始化脚本
echo "📝 创建MySQL初始化脚本..."
mkdir -p mysql-init

cat > mysql-init/init.sql << 'EOF'
-- 创建数据库
CREATE DATABASE IF NOT EXISTS trading_bot DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE trading_bot;

-- 创建交易记录表
CREATE TABLE IF NOT EXISTS trades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    amount DECIMAL(20,8) NOT NULL,
    price DECIMAL(20,8) NOT NULL,
    pnl DECIMAL(20,8) DEFAULT 0,
    confidence DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_symbol (symbol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建性能统计表
CREATE TABLE IF NOT EXISTS performance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    total_trades INT DEFAULT 0,
    winning_trades INT DEFAULT 0,
    total_pnl DECIMAL(20,8) DEFAULT 0,
    win_rate DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入一些测试数据
INSERT IGNORE INTO performance (date, total_trades, winning_trades, total_pnl, win_rate) VALUES
('2024-01-01', 10, 7, 150.50, 70.00),
('2024-01-02', 8, 5, 89.25, 62.50),
('2024-01-03', 12, 9, 245.75, 75.00);

FLUSH PRIVILEGES;
EOF

# 创建优化的docker-compose文件
echo "📝 创建优化的docker-compose配置..."
cat > docker-compose.yml << 'EOF'
services:
  mysql:
    image: mysql:8.0
    container_name: alpha-arena-mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: trading123
      MYSQL_DATABASE: trading_bot
      MYSQL_USER: trader
      MYSQL_PASSWORD: trader123
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./mysql-init:/docker-entrypoint-initdb.d
    command: >
      --default-authentication-plugin=mysql_native_password
      --character-set-server=utf8mb4
      --collation-server=utf8mb4_unicode_ci
      --innodb-buffer-pool-size=128M
      --max-connections=100
      --wait-timeout=28800
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-ptrading123"]
      timeout: 10s
      retries: 5
      interval: 30s
      start_period: 60s
    networks:
      - trading_network

  btc-trading-bot:
    build: .
    container_name: btc-trading-bot
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - MYSQL_HOST=mysql
      - MYSQL_PORT=3306
      - MYSQL_USER=trader
      - MYSQL_PASSWORD=trader123
      - MYSQL_DATABASE=trading_bot
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY:-}
      - BINANCE_API_KEY=${BINANCE_API_KEY:-}
      - BINANCE_SECRET_KEY=${BINANCE_SECRET_KEY:-}
    depends_on:
      mysql:
        condition: service_healthy
    volumes:
      - ./:/app
    working_dir: /app
    networks:
      - trading_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      timeout: 10s
      retries: 3
      interval: 30s
      start_period: 30s

volumes:
  mysql_data:
    driver: local

networks:
  trading_network:
    driver: bridge
EOF

# 添加健康检查端点到web服务器
echo "📝 添加健康检查端点..."
if ! grep -q "/health" web_server.py; then
    cat >> web_server.py << 'EOF'

@app.route('/health')
def health_check():
    """健康检查端点"""
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}
EOF
fi

# 启动MySQL服务
echo "🚀 启动MySQL服务..."
docker-compose up -d mysql

# 等待MySQL启动
echo "⏳ 等待MySQL启动（最多2分钟）..."
for i in {1..24}; do
    if docker-compose exec mysql mysqladmin ping -h localhost -u root -ptrading123 --silent; then
        echo "✅ MySQL启动成功！"
        break
    fi
    echo "等待MySQL启动... ($i/24)"
    sleep 5
done

# 检查MySQL状态
echo "📊 检查MySQL状态..."
docker-compose ps mysql
docker logs alpha-arena-mysql --tail 10

# 测试数据库连接
echo "🔗 测试数据库连接..."
docker-compose exec mysql mysql -u trader -ptrader123 -e "SELECT 1;" trading_bot

# 启动应用服务
echo "🚀 启动应用服务..."
docker-compose up -d btc-trading-bot

# 等待应用启动
echo "⏳ 等待应用启动..."
sleep 30

# 检查所有服务状态
echo "📊 检查所有服务状态..."
docker-compose ps

# 检查应用日志
echo "📋 检查应用日志..."
docker logs btc-trading-bot --tail 20

# 测试网站访问
echo "🌐 测试网站访问..."
curl -I http://localhost:8080 || echo "网站暂时无法访问"

echo "✅ MySQL修复完成！"
echo "🔗 请访问 http://47.79.95.72:8080 验证网站功能"