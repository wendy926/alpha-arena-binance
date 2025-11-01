# Alpha Arena - 加密货币AI交易机器人 🤖

基于 DeepSeek AI 与 OKX 永续合约接口的智能加密货币交易机器人，结合技术指标与市场情绪分析，提供可视化监控与模拟交易能力。

## ✨ 核心特性

### 🧠 AI 智能决策
- **DeepSeek 模型**分析市场趋势
- **技术指标**：SMA、EMA、MACD、RSI、布林带等
- **市场情绪**：集成 CryptoOracle 情绪数据 API
- **防频繁交易**：智能信号过滤，避免过度交易

### 📊 技术分析
- 移动平均线（5/20/50 周期）
- MACD 指标及信号线
- RSI 相对强弱指数
- 布林带及位置分析
- 支撑/阻力位计算
- 成交量分析

### 🌐 Web 监控面板
- **AI 模型状态监控**：实时显示模型与连接状态
- **账户信息与持仓展示**（模拟模式下提供纸上持仓）
- **收益曲线**：权益、盈亏与收益率可视化
- **专业 K 线图**（ECharts，支持缩放拖动）
- **AI 决策与交易记录追踪**
- **盈亏统计与信号分布分析**
- **深色主题与移动端响应式**

### 🔒 风险管理
- 杠杆交易支持（可配置）
- 止损/止盈自动设置
- 保证金检查（测试模式下不真实下单）
- 信心等级过滤
- 持仓跟踪（含动态回退纸上持仓）

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Docker & Docker Compose (可选)

### 1. 克隆项目
```bash
git clone https://github.com/your-username/alpha-arena-okx.git
cd alpha-arena-okx
```

### 2. 配置环境变量
```bash
cp .env_template .env
# 编辑 .env 文件，配置 DeepSeek API 密钥和 OKX API 密钥
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 启动服务
```bash
# 方式1：直接启动
python web_server.py

# 方式2：使用Docker
docker-compose up -d
```

### 5. 访问应用
- Web界面: http://localhost:8080
- API服务: http://localhost:8080/api

## 📁 项目结构

```
alpha-arena-okx/
├── deepseekok2.py           # 核心交易逻辑
├── web_server.py            # Web服务器
├── paper_trading.py         # 模拟交易模块
├── mock_ccxt.py             # 模拟交易所接口
├── init_sqlite.py           # SQLite数据库初始化
├── static/                  # 静态资源
│   ├── css/style.css       # 样式文件
│   └── js/app.js           # 前端JavaScript
├── templates/               # HTML模板
│   └── index.html          # 主页面
├── scripts/                 # 脚本目录
├── docs/                    # 项目文档
├── docker-compose.yml       # Docker编排文件
├── Dockerfile              # Docker镜像构建文件
├── requirements.txt        # Python依赖
├── .env_template           # 环境变量模板
└── README.md               # 项目说明
```

## 🔧 主要功能

### 🤖 AI交易决策
- DeepSeek AI模型分析市场趋势
- 技术指标综合分析
- 智能信号过滤
- 风险评估与管理

### 📊 Web监控界面
- 实时交易数据展示
- AI决策历史记录
- 收益曲线可视化
- 交易统计分析

### 🔌 API接口
- `/api/dashboard` - 仪表板数据
- `/api/trades` - 交易记录
- `/api/ai_decisions` - AI决策记录
- `/api/performance` - 绩效统计

## ⚙️ 配置说明

### 环境变量
复制 `.env_template` 为 `.env` 并配置以下参数：

```bash
# DeepSeek AI配置
DEEPSEEK_API_KEY=your_deepseek_api_key

# OKX API配置
OKX_API_KEY=your_okx_api_key
OKX_SECRET_KEY=your_okx_secret_key
OKX_PASSPHRASE=your_okx_passphrase

# 交易配置
TRADING_ENABLED=false  # 是否启用实际交易
TEST_MODE=true         # 测试模式开关
```

## 🐳 Docker部署

### 使用Docker Compose
```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 📝 开发指南

### 本地开发
```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python init_sqlite.py

# 启动服务
python web_server.py
```

## 🔍 故障排除

### 常见问题
1. **依赖安装问题**: 运行 `./install_all_deps.sh`
2. **数据库问题**: 运行 `python init_sqlite.py`
3. **端口占用**: 修改 `web_server.py` 中的端口配置

## 📄 许可证

MIT License

---

**注意**: 本项目仅供学习和研究使用，实际交易存在风险，请谨慎使用。