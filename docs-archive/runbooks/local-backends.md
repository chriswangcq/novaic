# 本地后端联调（Runbook）

桌面 **`novaic-app`** 内嵌 VmControl；本地联调时可以按需启动一组 Python 后端。端口约定见 **`novaic-common/config/services.json`** 与 [`../architecture/overview.md`](../architecture/overview.md)。

## 方式 A：`novaic-app` 配套 `start-backends.sh`

在 **`novaic-app`** 子模块内（在启动 **NovAIC.app / `tauri dev`** 之前）：

```bash
cd novaic-app/scripts
./start-backends.sh              # 启动本地核心子集
./start-backends.sh --stop       # 停止本地核心子集
./start-backends.sh --status     # 查看本地核心子集状态
```

该脚本当前只启动本地桌面核心子集：Gateway 19999、Queue Service 19997、Blob Service 19995，以及 Agent Runtime workers。它**不会**启动 Entangled、Business、Device、Cortex 或 Sandboxd；如果要测试依赖这些服务的 agent/runtime 流程，需要先用其他方式启动这些服务，否则 workers 会在日志里出现连接错误。完整逻辑以 `novaic-app/scripts/start-backends.sh` 文件注释为准。

## 方式 B：只跑客户端 UI

不需要本地 Gateway 时：

```bash
cd novaic-app
npm run dev
```

见 [`local-dev.md`](local-dev.md)。

## 生产级脚本

仓库根 `scripts/start.sh` 是 Linux / Cloud 生产启动脚本，由 `./deploy` 同步到服务器后执行。它依赖 `/opt/novaic/services`、`/opt/novaic/data` 和服务 venv 布局，不再作为本地开发启动入口。

## 相关

- [`local-dev.md`](local-dev.md) — 前端 / Tauri 开发命令  
- [`deploy.md`](deploy.md) — 远端部署（非本地）  
- [`../architecture/overview.md`](../architecture/overview.md) — 组件与端口表  
