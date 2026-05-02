# 本地后端联调（Runbook）

桌面 **`novaic-app`** 内嵌 VmControl；**Python 后端**（Gateway、Cortex、Agent Runtime、文件服务等）通常需**单独启动**。端口约定见 **`novaic-common/config/services.json`** 与 [`../architecture/overview.md`](../architecture/overview.md)。

## 方式 A：`novaic-app` 配套 `start-backends.sh`

在 **`novaic-app`** 子模块内（在启动 **NovAIC.app / `tauri dev`** 之前）：

```bash
cd novaic-app/scripts
./start-backends.sh              # 启动后端
./start-backends.sh --stop       # 停止
./start-backends.sh --status     # 状态
```

脚本内端口与 **Tauri 常量**对齐（Gateway 19999、Queue 19997、Business 19998（中枢编排）、Device 19993（设备服务）、File 19995 等）。完整逻辑见该文件注释。

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
