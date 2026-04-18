# 本地后端联调（Runbook）

桌面 **`novaic-app`** 内嵌 VmControl；**Python 后端**（Gateway、Cortex、Agent Runtime、文件服务等）通常需**单独启动**。端口约定见 **`novaic-common/config/services.json`** 与 [`../architecture/overview.md`](../architecture/overview.md)。

## 方式 A：仓库根 `scripts/start-all.sh`

在**父仓库根目录**，已初始化子模块并装好各目录下 **venv** 时：

```bash
cd /path/to/novaic
./scripts/start-all.sh           # 默认：源码 dev 模式（python -m）
./scripts/start-all.sh --dev     # 显式 dev
./scripts/start-all.sh --binary  # 若 scripts/dist/ 存在则走二进制
```

**Dev 模式**大致会拉起（并 `pkill` 同类旧进程）：

- Gateway `http://127.0.0.1:19999` — `novaic-gateway` 内 `python main_gateway.py`
- File Service `19995` — `novaic-storage-a` 内 `python -m file_service.main --port 19995`
- Cortex `19996` — `python -m novaic_cortex.main_cortex`
- Agent Runtime — `scheduler` + `task-worker`（日志在 `NOVAIC_DATA_DIR`，默认 `~/.novaic/logs/`）

健康检查 URL 见脚本末尾输出。

> **端口注意**：Cortex 与 Tauri 侧 **VmControl** 在配置里都常见 **19996**。若同时跑 App 内嵌控制与脚本起的 Cortex，需调整端口或只启其一（见 overview 中的说明）。

## 方式 B：`novaic-app` 配套 `start-backends.sh`

在 **`novaic-app`** 子模块内（在启动 **NovAIC.app / `tauri dev`** 之前）：

```bash
cd novaic-app/scripts
./start-backends.sh              # 启动后端
./start-backends.sh --stop       # 停止
./start-backends.sh --status     # 状态
```

父仓库亦有一份镜像脚本：`scripts/submodules/novaic-app/start-backends.sh`（与上逻辑一致时可任选其一）。

脚本内端口与 **Tauri 常量**对齐（Gateway 19999、Queue 19997、Business 19998（中枢编排）、Device 19993（设备服务）、File 19995 等）。完整逻辑见该文件注释。

## 方式 C：只跑客户端 UI

不需要本地 Gateway 时：

```bash
cd novaic-app
npm run dev
```

见 [`local-dev.md`](local-dev.md)。

## 相关

- [`local-dev.md`](local-dev.md) — 前端 / Tauri 开发命令  
- [`deploy.md`](deploy.md) — 远端部署（非本地）  
- [`../architecture/overview.md`](../architecture/overview.md) — 组件与端口表  
