# 架构核查报告（8 路并行，2026-04）

> 由 8 名只读 explore subagent 分别对照 **代码与脚本** 核查后合并。用于补全「小改动」未覆盖的运维/配置真相；与 `docs/agent-handoff-context.md`、`docs/backend-architecture.md` 交叉引用。  
> **权威仍以一提交内的源码为准**；本文记录核查时的仓库快照结论。  
> **全库文档索引**（必读 / 子系统 / 目录约定）：见 [docs/README.md](README.md)。

---

## 1. 执行摘要

| 主题 | 结论 |
|------|------|
| **业务实体（agents、messages 等）** | 持久化在 **Entangled Service** 的 SQLite（默认 `data/entangled.db`，见 `entangled-service`）；Gateway 通过 `EntangledClient` 访问。 |
| **Gateway `gateway.db`（schema v63）** | 仅 **operational** 表：`config`、`entangled_sync_versions`、`pending_questions`、`question_responses`、`ssh_keys`、`vm_processes`、`pc_clients`、`subagent_context`。`agents` / `chat_messages` 等在迁移中 **DROP**（`_SHADOW_AND_DEAD_TABLES`），**不是**当前业务主表。 |
| **Cortex HTTP** | 默认 **`CORTEX_PORT=19996`**（`novaic-cortex/novaic_cortex/main_cortex.py`）；路由以 **`/v1/...`** 为主，`GET /health`。启动需 **阿里云 OSS** 环境变量（`ALIBABA_CLOUD_ACCESS_KEY_ID` / `SECRET` 等）。 |
| **Cortex URL 与 ServiceConfig** | **`novaic-common/config/services.json` 无 `cortex` 段**；Agent-Runtime 用环境变量 **`NOVAIC_CORTEX_URL`**（默认 `http://127.0.0.1:19996`，见 `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`）。 |
| **端口冲突** | `services.json` 中 **`vmcontrol` 与 Cortex 均可能占用 19996**；同机部署必须改端口或只跑其一。 |
| **Runtime Orchestrator** | 父仓库 **无** `novaic-runtime-orchestrator/` 包；`main_gateway.py` 的 `--runtime-orchestrator-url` **被 SUPPRESS 且未写入 ServiceConfig**。 |
| **Tools Server** | 父仓库 **无** `novaic-tools-server/`；`novaic-agent-runtime/main_novaic.py tools-server` 仅当设置 **`NOVAIC_TOOLS_SERVER_SPLIT_REPO`** 且存在 `main_tools.py`。`./deploy tools` 仍会 rsync 该目录名 → **无目录则部署失败**。 |
| **deploy `services` vs `start.sh`** | `deploy services` rsync：`novaic-common`、`novaic-gateway`、`novaic-agent-runtime`、`novaic-storage-a`、`novaic-cortex`、**`Entangled`**（子模块）。**`scripts/start.sh`（服务端）** 启动 gateway、queue、file、cortex、workers；**未**单独起 **`entangled-service` HTTP 进程**——与「Entangled 为独立 :19900 服务」的文档叙述需按环境区分：生产可能把实体引擎嵌入其他布局，或需单独运维 `entangled-service`（见 `entangled-service/main.py`）。 |
| **脚本漂移** | `scripts/start-all.sh` 的 dev/binary 模式**未**启动 queue :19997，却给 worker 指向 19997；`novaic-app/scripts/start-backends.sh` 与云端 `start.sh` 在 **Cortex / Tools** 上不一致。 |

---

## 2. Gateway（`novaic-gateway`）

- **入口**：`main_gateway.py`；默认端口 **19999**。
- **必填 CLI**：`--data-dir`、`--queue-service-url`、`--file-service-url`。
- **Internal API**：`gateway/api/internal_proxy.py` 聚合 **`/internal`** 下 message、subagent、agent、task、config、pc_client（含 **`/internal/pc/ws`**）。
- **实体 action**：`POST /api/entities/{entity}/action/{action_name}`（见 `entities.py`）。
- **Lifespan**：`init_database` → `register_all_entities()` → **`register_with_entangled_service()`**（`POST /v1/schema/register`）→ VM 恢复等。
- **`MessageRepository`**：`gateway/entity/repos/message.py` 经 **`get_entangled_client()`** 访问实体 **`messages`**，注释说明存储在 Entangled。
- **易错文档**：称「Gateway SQLite 含 agents/chat_messages 表且为权威」→ **与 v63 迁移矛盾**。

---

## 3. Entangled 栈

- **`Entangled/`**（子模块）：协议与 Python server 包路径；**`entangled-service/`** 为可部署 HTTP 服务，默认 **`ENTANGLED_PORT=19900`**，`ENTANGLED_DB_PATH` 默认 `data/entangled.db`。
- **WS**：Entangled 服务端 **`/v1/sync`**（`entangled_service/app.py`）；Gateway 文档若写「WS 在 Gateway 上」易混淆——以 **entangled-service** 为准。

---

## 4. Cortex（`novaic-cortex`）

- **对外 API 面**：`novaic-cortex/novaic_cortex/api.py` — `/v1/shell`、`/v1/proxy/{command}`、`/v1/context/*`、`/v1/scope/*`、若干 **`/v1/internal/*`**（供 runtime 无 JWT 调用）等。
- **Agent-Runtime**：`CortexBridge` → `httpx` POST 至上述端点；**`NOVAIC_CORTEX_ENABLED`** 可关闭。
- **疑点（需代码跟进）**：`novaic-agent-runtime/task_queue/workers/watchdog_sync.py` 对 `/v1/ls` 使用 `Authorization: Bearer internal`，而 `novaic-cortex/novaic_cortex/api.py` 中 `/v1/ls` 走 JWT 校验 — **可能无效**，依赖 fallback 路径。

---

## 5. Agent-Runtime（`novaic-agent-runtime`）

- **`novaic-agent-runtime/main_novaic.py` 模式**：`gateway`、`queue-service`、`watchdog`、`task-worker`、`saga-worker`、`health`、`scheduler`、`vmcontrol` 为**活跃**；`tools-server`（分拆仓）、`file-service` / `tool-result-service` 为 **stub 退出**（指向 `novaic-storage-a` / TRS 已移除）。
- **Handlers**：`novaic-agent-runtime/task_queue/handlers/*.py` 由 **本仓库唯一** 实际注册执行；**无** orchestrator 进程并行执行同一套 handler。

---

## 6. `ServiceConfig`（`novaic-common` 暴露的 URL）

| `services.json` 键 | `ServiceConfig` |
|--------------------|-----------------|
| gateway, queue_service, tools_server, vmcontrol, file_service, tool_result_service, entangled_service | 有 host/port/url |
| **cortex** | **无** |

Cortex 与 LLM Factory 等需依赖 **环境变量** 或各进程自有 `config`，**未**统一进 `services.json`。

---

## 7. 部署与脚本（摘要）

| 路径 | 行为摘要 |
|------|----------|
| `./deploy` | 子命令含 **`gateway` `runtime` `tools` `storage-a` `cortex` `services` `relay` `factory`** 等；**无 `orchestrator`**。 |
| `./deploy tools` | rsync **`novaic-tools-server`** — 与 HANDOVER「已退役」不一致；根目录无该目录时失败。 |
| `scripts/start.sh` | 云端典型：gateway 19999、queue 19997、file 19995、cortex 19996、workers；**无 tools**、**无 RO**。 |
| `scripts/start-all.sh` | dev 与 binary 模式对 **cortex vs tools-server** 二选一；**queue 19997 常未启动** |

---

## 8. 文档债（未在本轮逐文件修改）

`docs/` 下仍有大量 **历史设计**（`19993`、RO、Tools Server 为必达等）的 **271+ 处** 命中（统计口径：仅 `docs/*.md` 或含 HANDOVER，以 `rg` 为准；含子模块镜像文档）。建议：

- **P1**： onboarding / E2E / control-plane — 已在本轮修正 `docs/runbooks/E2E_READINESS.md` 等入口。
- **P2**：设计文档中的 Gateway→Tools 箭头 — 加页眉 **「历史方案」**；`docs/archived/` 已从当前树移除（非工作区目录）；历史内容：`git show docs-graveyard-p2:docs/archived/`（tag `docs-graveyard-p2`）。
- **P4–P5**：`docs/research/` 等仍含历史路径引用；`docs/submodules/*` 仅 **README**，**不要**当现行架构。

---

## 9. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-04-09 | 初版：8 路 subagent 核查合并；驱动 `backend-architecture.md`、`HANDOVER.md`、`runbooks/E2E_READINESS.md` 等修订 |
