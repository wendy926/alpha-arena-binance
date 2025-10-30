# Alpha Arena SQLite版本设置指南

## 🚀 快速启动

### 方法1: 一键修复脚本
```bash
chmod +x fix_sqlite_and_deps.sh
./fix_sqlite_and_deps.sh
```

### 方法2: 分步执行
```bash
# 1. 安装依赖
chmod +x install_deps.sh
./install_deps.sh

# 2. 修复数据库表结构
python3 check_db_schema.py

# 3. 初始化数据库
python3 init_sqlite.py

# 4. 启动web服务器
python3 web_server.py
```

## 🔧 问题解决

### 问题1: `table trades has no column named symbol`
**原因**: 旧的数据库表结构不匹配
**解决**: 运行 `python3 check_db_schema.py` 重建表结构

### 问题2: `ModuleNotFoundError: No module named 'flask'`
**原因**: 缺少Python依赖包
**解决**: 运行 `./install_deps.sh` 安装依赖

### 问题3: 权限问题
**解决**: 
```bash
chmod +x *.sh
```

## 📊 数据库信息

- **数据库类型**: SQLite
- **数据库文件**: `./data/paper_trades.db`
- **表结构**:
  - `trades`: 交易记录表
  - `positions`: 持仓记录表

## 🌐 访问地址

启动成功后访问: http://localhost:8080

## 📝 配置文件

项目已配置使用SQLite，相关配置在 `.env` 文件中：
```
DB_TYPE=sqlite
SQLITE_DB_PATH=./data/paper_trades.db
```

## 🎯 优势

- ✅ 无需Docker容器
- ✅ 轻量级数据库
- ✅ 避免MySQL重启问题
- ✅ 数据持久化存储