> **文档说明**：本地/联调 **E2E 启动顺序**的现行指引；权威拓扑仍以 `docs/backend-architecture.md` 为准。

# 端到端测试就绪说明

> **2026-04 重写**：与当前父仓库布局一致（无 `novaic-runtime-orchestrator`、无根目录 `novaic-tools-server`；实体在 **Entangled**；认知在 **Cortex**）。旧版基于 RO + Tools + Storage B + TRS 二进制 的段落已作废。详见 **`docs/architecture-verification-2026-04.md`**。

## 一、Build / 二进制

若使用 `build-all.sh` 或各子仓构建，**当前主线**常见产物与 **旧文档**差异：

| 组件 | 说明 |
|------|------|
| ~~novaic-runtime-orchestrator~~ | **不在父仓库**；勿再编排 `:19993` RO |
| ~~novaic-tools-server~~ | **不在父仓库**；工具由 `novaic-agent-runtime` handlers + Cortex |
| ~~novaic-storage-b / TRS~~ | TRS 已移除；勿再依赖 `:19994` tool-result-service |
| **novaic-storage-a** | File Service（`:19995`） |
| **novaic-gateway** | Gateway `:19999` |
| **novaic-agent-runtime** | Queue + Workers 等 |
| **novaic-cortex** | Cortex HTTP `:19996`（与 **vmcontrol** 同端口时需改环境变量） |

---

## 二、推荐本地/联调启动顺序（概念）

以下端口为 **默认**；请以各进程 `--help` 与 `ServiceConfig` 为准。

1. **Entangled Service**（实体权威）`:19900`  
   `cd entangled-service && python main.py`（或等价 uvicorn；见该目录 README）

2. **File Service（novaic-storage-a）** `:19995`

3. **Queue Service** `:19997`  
   `python main_novaic.py queue-service --host 127.0.0.1 --port 19997 --data-dir "$DATA_DIR"`

4. **Cortex** `:19996`  
   需配置 OSS 相关环境变量（见 `novaic_cortex/main_cortex.py`）。  
   Worker 侧：`NOVAIC_CORTEX_URL=http://127.0.0.1:19996`

5. **Gateway** `:19999`  
   **不要**再传 `--runtime-orchestrator-url`（`main_gateway.py` 中该参数被 suppress，且不写入 ServiceConfig）。  
   必填：`--data-dir`、`--queue-service-url`、`--file-service-url`。  
   `--tools-server-url` 仅 deprecated 兼容，多数场景可省略。

6. **Workers**（`novaic-agent-runtime`）：`watchdog`、`task-worker`、`saga-worker`、`health`（按需 `scheduler`）  
   **不要**再传 `--runtime-orchestrator-url`（若 CLI 仍接受，以当前 `main_novaic.py` 为准 — 许多路径已不再使用）。

**可选**：独立 **Tools HTTP**（仅当分拆仓存在 `main_tools.py`）：设置 `NOVAIC_TOOLS_SERVER_SPLIT_REPO` 后 `main_novaic.py tools-server`。

**脚本注意**：`scripts/start-all.sh` 的 dev/binary 模式**可能未启动 queue-service**，却仍向 worker 指向 `:19997` — 联调前请确认 queue 已监听。云端参考 **`scripts/start.sh`**（与 `deploy services` 配套）。

---

## 三、健康检查（示例）

```bash
curl -s http://127.0.0.1:19999/api/health    # Gateway
curl -s http://127.0.0.1:19997/health       # Queue（路径以 queue_service 为准）
curl -s http://127.0.0.1:19996/health       # Cortex
curl -s http://127.0.0.1:19995/health       # File service（若实现 /health）
# Entangled：见 entangled-service 路由
```

**勿再使用**：`19993` RO、`19994` TRS、无条件的 `19998` Tools（除非你真的起了分拆 tools 进程）。

---

## 四、参考文档

- `docs/architecture-verification-2026-04.md` — 配置与部署核查
- `docs/agent-handoff-context.md` — Gateway / Entangled / Cortex / Runtime 分工
- `scripts/submodules/novaic-gateway/smoke_gateway_repo_root.sh` — Gateway 冒烟（父仓库路径；**非** `novaic-gateway/scripts/` 下）
- **CI**：根目录 `.github/workflows/tauri-ci.yml` 跑前端 Vitest/tsc、Gateway `unittest … test_sync_contract_schema` 等；**非**全栈多服务 E2E 矩阵
