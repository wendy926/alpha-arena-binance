# Alpha Arena – Binance 版 BTC 自动交易机器人 🤖

基于 DeepSeek / Qwen AI 与 Binance USDT-M 永续接口的智能加密货币交易机器人，结合技术指标与市场情绪分析，提供可视化监控与模拟交易能力。

---

## ✨ 核心特性

### 🧠 AI 智能决策
- DeepSeek / Qwen 模型分析市场趋势
- 技术指标：SMA、EMA、MACD、RSI、布林带等
- 市场情绪：集成 CryptoOracle 情绪数据 API
- 防频繁交易：智能信号过滤，避免过度交易

### 📊 技术分析
- 移动平均线（5/20/50 周期）
- MACD 指标及信号线
- RSI 相对强弱指数
- 布林带及位置分析
- 支撑/阻力位计算
- 成交量分析

### 🌐 Web 监控面板
- AI 模型状态监控：实时显示模型与连接状态
- 账户信息与持仓展示（模拟模式下提供纸上持仓）
- 收益曲线：权益、盈亏与收益率可视化
- 专业 K 线图（ECharts，支持缩放拖动）
- AI 决策与交易记录追踪
- 盈亏统计与信号分布分析
- 深色主题与移动端响应式

### 🔒 风险管理
- 杠杆交易支持（可配置）
- 止损/止盈自动设置
- 保证金检查（测试模式下不真实下单）
- 信心等级过滤
- 持仓跟踪（含动态回退纸上持仓）

---

## 🚀 快速开始

### 1. 环境要求

- Python 3.11（或使用 Docker 运行）
- Windows / Linux / macOS
- 依赖见 `requirements.txt`

### 2. 部署方式

提供两种部署方式，任选其一：

#### 方式一：Docker 部署 🐳（推荐）

优势：无需安装 Python，一键启动，环境隔离。

```bash
# 1) 克隆项目
git clone https://github.com/wendy926/alpha-arena-binance.git
cd alpha-arena-binance

# 2) 创建配置文件
cp .env_template .env
# 编辑 .env 文件，填入你的 AI 模型密钥（DeepSeek/Qwen）

# 3) 启动容器
docker-compose up -d

# 4) 查看日志
docker-compose logs -f

# 5) 停止服务
docker-compose down
```

访问地址：`http://localhost:8080`

常用命令：

```bash
docker-compose ps            # 查看运行状态
docker-compose restart       # 重启服务
docker-compose exec btc-trading-bot bash  # 进入容器调试
docker-compose logs -f --tail=100         # 查看实时日志
```

#### 方式二：Python 虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate    # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
python web_server.py
```

---

## ⚙️ 配置文件

在项目根目录创建 `.env` 文件：

```env
# AI 模型选择（deepseek 或 qwen）
AI_PROVIDER=deepseek

# DeepSeek API（默认）
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx

# 阿里百炼 Qwen（可选）
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx

# 说明：当前实现默认以测试模式运行（不读取交易所 API 密钥、不执行真实下单）。
# 如需启用实盘交易，请在代码中为 ccxt.binanceusdm 注入 apiKey/secret，详见下文。
```

详细配置说明：`ENV_CONFIG.md`（模板仍包含 OKX 示例；实际实现以 Binance USDT-M 永续为主）。

### 启用实盘交易（可选）

当前代码默认 `TRADE_CONFIG['test_mode'] = True`，不会真实下单。若需实盘：

```python
# 在 deepseekok2.setup_exchange 中配置：
exchange = _ccxt.binanceusdm({
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_SECRET'),
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})
```

并将 `TRADE_CONFIG['test_mode']` 设为 `False`，谨慎使用。

---

## 🔄 交易参数

编辑 `deepseekok2.py` 中的配置：

```python
TRADE_CONFIG = {
    'symbol': 'BTC/USDT',       # Binance USDT-M 永续交易对
    'amount': 0.01,             # 每次交易数量(BTC)
    'leverage': 10,             # 杠杆倍数
    'timeframe': '15m',         # K线周期
    'test_mode': True,          # True=模拟 False=实盘（默认模拟）
    'data_points': 96,          # 分析数据点数（近24小时）
}
```

建议：保守参数起步，实盘前充分验证端到端流程。

---

## 🧩 实现逻辑概览（与实际代码一致）

- 行情数据：优先使用 `ccxt.binanceusdm` 获取 USDT-M 永续数据，失败时回退到现货或本地模拟 OHLCV。
- 收益曲线：每次执行都会追加数据点；若 `fetch_balance` 失败，使用模拟权益与纸上持仓的 `unrealized_pnl` 合成收益点，`initial_balance` 默认 10000 USDT。
- 持仓信息：优先尝试真实持仓获取，失败时动态回退到 `compute_paper_position`（Web `/api/dashboard` 端点在请求时也会进行此回退）。
- 执行周期：`main()` 启动后循环执行，`trading_bot()` 在整点运行并内部等待下一周期。

### Web 接口

- `/api/dashboard` – 仪表盘数据（含 `current_position` 回退）
- `/api/profit_curve` – 收益曲线数据
- `/api/ai_model_info` – AI 模型与连接状态
- `/api/trades` – 交易记录
- `/api/ai_decisions` – AI 决策历史
- `/api/health` – 公共 API 连通性检查（Binance/OKX Ping）

> 说明：当前代码默认开启测试模式；如需实盘请谨慎配置并在小仓位下验证。

---

## 🛠️ 开发与运维

常见操作：

```bash
# 启动 Web 服务（本地）
python web_server.py

# 检查健康状态（容器内）
curl http://localhost:8080/api/health
```

日志中若出现 Binance AuthenticationError，多为未配置 `apiKey/secret`，此时将自动进入模拟逻辑并仍提供可用的 Web 面板数据。

---

## 📚 相关链接

- DeepSeek 官网：https://www.deepseek.com/
- DeepSeek 平台：https://platform.deepseek.com/
- DeepSeek 文档：https://platform.deepseek.com/docs

- 阿里百炼（DashScope）：https://dashscope.console.aliyun.com/
- Qwen 文档：https://help.aliyun.com/zh/dashscope/

- Binance 官网：https://www.binance.com/
- Binance Futures API 文档：https://developers.binance.com/docs/derivatives/USDT-Margined-Futures/overview

---

## 🔁 GitHub 仓库重命名与本地远端更新

1) 在 GitHub 仓库设置中将项目名改为 `alpha-arena-binance`（Settings → General → Repository name）。

2) 本地更新远端地址：

```bash
git remote set-url origin https://github.com/wendy926/alpha-arena-binance.git
git remote -v  # 验证
```

完成后，正常执行：`git push origin main`。