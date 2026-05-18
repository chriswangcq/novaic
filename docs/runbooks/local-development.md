# 本地开发环境搭建

## 前置条件

| 工具 | 版本要求 | 说明 |
|------|----------|------|
| Node.js | >= 18 | 前端构建 |
| npm | >= 9 | 包管理 |
| Rust (rustup) | stable | Tauri + VmControl 编译 |
| Python | >= 3.10 | 后端服务 |
| Redis | 最新稳定版 | Cortex scope lock |
| Xcode CLT | 最新 | macOS: `xcode-select --install` |

## 仓库初始化

```bash
git clone --recursive <repo-url>
cd new-build-novaic

# 初始化所有子模块
git submodule update --init --recursive
```

## 前端开发

### 只跑前端（无 Tauri）

```bash
cd novaic-app
npm install
npm run dev
```

浏览器访问 `http://localhost:5173`。

### 完整桌面应用（含 Rust / VmControl）

```bash
cd novaic-app
npm install
npm run tauri:dev
```

## 后端服务启动

### 方式 A：start-backends.sh（推荐）

在 novaic-app 子模块内：

```bash
cd novaic-app/scripts
./start-backends.sh              # 启动本地核心子集
./start-backends.sh --stop       # 停止
./start-backends.sh --status     # 查看状态
```

该脚本启动本地核心子集：Gateway :19999、Queue Service :19997、Blob Service :19995、Agent Runtime workers。

**不启动**的服务：Entangled、Business、Device、Cortex、Sandboxd。如需测试依赖这些服务的流程，需单独启动。

### 方式 B：手动启动单个服务

每个 Python 服务的启动方式类似：

```bash
cd novaic-<service>
python -m venv .venv
source .venv/bin/activate
pip install -e .
# 启动命令因服务而异，参考各服务 README 或 pyproject.toml [project.scripts]
```

### 服务端口约定

参考 `novaic-common/config/services.json`，详见 [端口与配置](../reference/ports-and-config.md)。

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| 端口 1420 被占用 | `kill $(lsof -ti:1420)` |
| 端口 5173 被占用 | `kill $(lsof -ti:5173)` |
| Tauri 编译失败 | 确认 Xcode CLT 已安装：`xcode-select --install` |
| npm install 失败 | 删除 node_modules 和 package-lock.json 后重试 |
| Python venv 问题 | 确认 Python >= 3.10，重建 venv |
| Worker 连接错误 | 检查依赖服务是否启动（Cortex、Device 等） |
| 构建桌面 release | 使用 `npm run tauri:build -- --bundles app`（非 `--ci`） |

## 相关文档

- [系统总览](../overview.md)
- [端口与配置](../reference/ports-and-config.md)
- [云端部署](deploy.md)
