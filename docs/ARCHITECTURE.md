# Alpha Arena 系统架构文档

## 概述

Alpha Arena 是一个基于微服务架构的加密货币交易机器人系统，采用前后端分离的设计模式，通过 Docker 容器化部署，实现高可用性和可扩展性。

## 整体架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Alpha Arena 系统                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │   前端服务       │    │   后端服务       │    │   数据库服务     │ │
│  │   React App     │◄──►│   Node.js API   │◄──►│   MySQL 5.7     │ │
│  │   Port: 3000    │    │   Port: 3001    │    │   Port: 3306    │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│                                │                                  │
│                                ▼                                  │
│                    ┌─────────────────┐                           │
│                    │   外部 API 服务  │                           │
│                    │   OKX Trading   │                           │
│                    │   API           │                           │
│                    └─────────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. 前端服务 (Frontend)

**技术栈**: React 18 + TypeScript + Vite

**主要功能**:
- 实时交易仪表板
- 交易历史查看
- 系统监控界面
- 策略配置管理

**核心模块**:
```
frontend/
├── src/
│   ├── components/          # 可复用组件
│   │   ├── Dashboard/       # 仪表板组件
│   │   ├── TradingView/     # 交易视图
│   │   └── Common/          # 通用组件
│   ├── pages/               # 页面组件
│   ├── services/            # API 服务
│   ├── hooks/               # 自定义 Hooks
│   ├── utils/               # 工具函数
│   └── types/               # TypeScript 类型定义
├── public/                  # 静态资源
└── package.json            # 依赖配置
```

**关键特性**:
- 响应式设计，支持移动端
- 实时数据更新 (WebSocket/Polling)
- 现代化 UI 组件库
- 类型安全的 TypeScript 开发

### 2. 后端服务 (Backend)

**技术栈**: Node.js + Express + TypeScript

**主要功能**:
- RESTful API 服务
- 交易逻辑处理
- 数据库操作
- 外部 API 集成

**核心模块**:
```
backend/
├── src/
│   ├── controllers/         # 控制器层
│   │   ├── dashboard.js     # 仪表板 API
│   │   ├── trades.js        # 交易 API
│   │   └── health.js        # 健康检查
│   ├── services/            # 业务逻辑层
│   │   ├── trading.js       # 交易服务
│   │   ├── database.js      # 数据库服务
│   │   └── okx.js           # OKX API 服务
│   ├── models/              # 数据模型
│   ├── middleware/          # 中间件
│   ├── config/              # 配置文件
│   └── utils/               # 工具函数
├── package.json            # 依赖配置
└── Dockerfile              # 容器配置
```

**API 端点**:
- `GET /api/dashboard` - 获取仪表板数据
- `GET /api/trades` - 获取交易记录
- `GET /api/health` - 系统健康检查
- `POST /api/trades` - 创建新交易
- `PUT /api/trades/:id` - 更新交易状态

### 3. 数据库服务 (Database)

**技术栈**: MySQL 5.7

**数据模型**:

```sql
-- 交易记录表
CREATE TABLE trades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    signal VARCHAR(20) NOT NULL,
    action VARCHAR(10) NOT NULL,
    amount DECIMAL(18,8) NOT NULL,
    price DECIMAL(18,8) NOT NULL,
    stop_loss DECIMAL(18,8),
    take_profit DECIMAL(18,8),
    confidence DECIMAL(5,2),
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 系统配置表
CREATE TABLE system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## 数据流架构

### 1. 请求处理流程

```
用户请求 → Nginx (可选) → Frontend → Backend API → Database → 外部 API
    ↓                                      ↓              ↓
响应返回 ← Frontend ← JSON Response ← Business Logic ← Data Processing
```

### 2. 交易执行流程

```
市场数据获取 → 策略分析 → 信号生成 → 风险评估 → 订单执行 → 结果记录
     ↓            ↓         ↓         ↓         ↓         ↓
  OKX API → 算法模块 → 信号队列 → 风险模块 → OKX API → Database
```

## 部署架构

### Docker Compose 配置

```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    
  backend:
    build: ./backend
    ports:
      - "3001:3001"
    environment:
      - NODE_ENV=production
      - MYSQL_HOST=mysql
    depends_on:
      - mysql
    
  mysql:
    image: mysql:5.7
    ports:
      - "3306:3306"
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=trading_bot
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:
```

### 容器网络

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │  frontend:3000  │    │  backend:3001   │    │  mysql:3306     │ │
│  │  (nginx)        │◄──►│  (node.js)      │◄──►│  (mysql)        │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│           │                       │                       │        │
└───────────┼───────────────────────┼───────────────────────┼────────┘
            │                       │                       │
            ▼                       ▼                       ▼
    Host:3000 (Web)        Host:3001 (API)        Host:3306 (DB)
```

## 安全架构

### 1. 数据安全
- 环境变量管理敏感信息
- 数据库连接加密
- API 密钥安全存储

### 2. 网络安全
- 容器间网络隔离
- 端口访问控制
- HTTPS 加密传输 (生产环境)

### 3. 应用安全
- 输入验证和清理
- SQL 注入防护
- 跨站脚本攻击 (XSS) 防护

## 监控和日志

### 1. 应用监控
- 健康检查端点
- 性能指标收集
- 错误追踪和报告

### 2. 日志管理
```
logs/
├── application.log          # 应用日志
├── trading.log             # 交易日志
├── error.log               # 错误日志
└── access.log              # 访问日志
```

### 3. 监控指标
- 系统资源使用率
- API 响应时间
- 交易成功率
- 数据库连接状态

## 扩展性设计

### 1. 水平扩展
- 无状态服务设计
- 负载均衡支持
- 数据库读写分离

### 2. 垂直扩展
- 资源配置优化
- 缓存策略实施
- 数据库索引优化

### 3. 微服务拆分 (未来规划)
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   用户服务       │  │   交易服务       │  │   数据服务       │
│   User Service  │  │ Trading Service │  │  Data Service   │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
                    ┌─────────────────┐
                    │   API 网关      │
                    │   API Gateway   │
                    └─────────────────┘
```

## 技术选型说明

### 前端技术选型
- **React**: 成熟的前端框架，生态丰富
- **TypeScript**: 类型安全，提高代码质量
- **Vite**: 快速的构建工具，开发体验好

### 后端技术选型
- **Node.js**: JavaScript 全栈开发，性能优秀
- **Express**: 轻量级 Web 框架，易于扩展
- **MySQL**: 成熟的关系型数据库，事务支持好

### 部署技术选型
- **Docker**: 容器化部署，环境一致性
- **Docker Compose**: 多容器编排，简化部署

## 性能优化

### 1. 前端优化
- 代码分割和懒加载
- 静态资源压缩
- 浏览器缓存策略

### 2. 后端优化
- 数据库连接池
- API 响应缓存
- 异步处理优化

### 3. 数据库优化
- 索引优化
- 查询优化
- 连接池配置

## 故障恢复

### 1. 备份策略
- 数据库定期备份
- 配置文件版本控制
- 容器镜像版本管理

### 2. 恢复流程
- 自动重启机制
- 数据恢复程序
- 服务降级策略

---

本文档将随着系统的发展持续更新，确保架构文档与实际实现保持一致。