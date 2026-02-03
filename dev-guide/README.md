# NovAIC 开发指南

本目录包含 NovAIC 项目的开发文档和工具。

## 文档结构

| 文件 | 内容 |
|------|------|
| **[smoke-test.md](./smoke-test.md)** | **冒烟测试指南（基准流程）** |
| [build-process.md](./build-process.md) | 构建与发布流程 |
| [run-dev.sh](./run-dev.sh) | 开发环境启动脚本 |

## 快速开始

### 1. 环境准备

```bash
# 克隆仓库
git clone https://github.com/novaic/novaic.git
cd novaic

# 安装 Gateway 依赖
cd novaic-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# 安装 Tauri 前端依赖
cd novaic-app
npm install
cd ..
```

### 2. 启动开发环境

```bash
# 方式 1: 使用脚本启动后端（后台 + /tmp/*.log）
./dev-guide/run-dev.sh

# 方式 2: 分步启动
./dev-guide/run-dev.sh gateway      # Gateway (19999)
./dev-guide/run-dev.sh mcp          # MCP Gateway (19998)
./dev-guide/run-dev.sh watchdog     # Watchdog (消息监听)
./dev-guide/run-dev.sh task         # Task Worker
./dev-guide/run-dev.sh saga         # Saga Worker
./dev-guide/run-dev.sh health       # Health Worker

# 方式 3: Tauri 开发模式 (自动启动所有后端)
cd novaic-app
npm run tauri dev
```

### 3. 验证服务状态

```bash
# Gateway 健康检查
curl http://127.0.0.1:19999/api/health

# MCP Gateway 健康检查
curl http://127.0.0.1:19998/api/health

# 查看任务状态
curl http://127.0.0.1:19999/internal/tq/tasks/stats
```

## 相关文档

- [冒烟测试](./smoke-test.md) - 基准流程与验证清单
- [构建流程](./build-process.md) - 构建与发布
