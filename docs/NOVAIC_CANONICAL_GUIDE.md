# NovAIC 父仓 — 权威阅读指南（单一入口）

> **目的**：用**一份**文档说清「读什么、不读什么、各组件关系」，避免在 `design/`、`research/`、`device/` 等大量过程稿中重复检索。  
> **性质**：**索引 + 摘要**；技术细节、端口证明与运维命令仍以链接文件与源码为准。  
> **更新**：与 `docs/backend-architecture.md`、`docs/architecture-verification-2026-04.md`、根目录 `HANDOVER.md` 冲突时，以**后者与代码**为准，并应回头修订本页摘要。

---

## 1. 文档分层（防冗余）

| 层级 | 读什么 | 不要重复读 |
|------|--------|------------|
| **L0 入口** | **本文件** + [`README.md`](README.md) | — |
| **L1 现行总览** | [`backend-architecture.md`](backend-architecture.md)、[`architecture-verification-2026-04.md`](architecture-verification-2026-04.md)、[`agent-handoff-context.md`](agent-handoff-context.md)、根目录 [`../HANDOVER.md`](../HANDOVER.md) | 不要在多份「总览」里各抄一份端口表；以 **verification** 为运维真相补丁 |
| **L2 子系统专章** | Cortex / Entangled / Sync：见下表 | 专章内部可能仍含时点表述，以页眉为准 |
| **L3 过程稿** | [`design/`](design/)、[`research/`](research/)、[`device/`](device/)、[`gateway-upgrade/`](gateway-upgrade/)、[`ota/`](ota/)、[`p2p/`](p2p/) 等 | **默认视为历史或方案讨论**；引用前看页眉；**不**与 L1 逐句对齐期望 |

**运维 Runbook（可执行）**：[`runbooks/`](runbooks/) — E2E、服务矩阵、热更新、环境类部署步骤；**与 L1 冲突时仍以 L1 + verification 为准**。

**重建与维护**：父仓 PR 使用 **`.github/pull_request_template.md`**；改协议 / 端口 / Entangled 订阅时请勾选其中「Documentation & contracts」并更新对应 `docs/`。

**树形索引**：[`TREE.md`](TREE.md) — `docs/` 下**完整物理目录树**（脚本生成）与 **DFS 从 L0 到最底层叶子**的阅读说明；大规模改目录后请重跑 `python3 docs/_scripts/generate_docs_tree.py`。

**原则**：需要「一条链路讲清楚」→ 先看 **L1**；需要「当时为什么这样设计」→ **L3**；需要「合并后的端口与运维补丁」→ **§3 本页汇总表 + verification**（两处互补，冲突以 verification 与代码为准）。

---

## 2. 逻辑拓扑（简图）

```
                    ┌─────────────────────────────────────────┐
                    │  桌面 / 移动端（novaic-app + Tauri）      │
                    │  Entangled WS / REST · AppBridge WS 等   │
                    └───────────┬─────────────────────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼
  ┌─────────────┐        ┌─────────────┐        ┌──────────────────┐
  │ Gateway     │        │ Entangled   │        │ Cortex (:19996)  │
  │ :19999      │◄──────►│ Service     │        │ Workspace / 工具  │
  │ operational │        │ :19900      │        │ S3-backed        │
  │ DB + internal      │ │ 实体 SQLite │        └────────┬─────────┘
  └──────┬──────┘        └─────────────┘                 │
         │                                                │
         ▼                                                │
  ┌─────────────┐        ┌───────────────────────────────┘
  │ Queue :19997│        │
  │ Task/Saga   │◄───────┘  Agent-Runtime Workers
  └─────────────┘           (tool_handlers · Sagas · Watchdog)
```

**说明**：RO（Runtime Orchestrator）与必选 Tools Server **已不作为主线**；若文档仍写 `:19993` 或「必达 Tools Server」，视为**历史表述**。工具执行见 `HANDOVER.md` §12.4。

---

## 3. 端口与配置（本页汇总表）

以下与 `novaic-common/config/services.json` 及典型 **`scripts/start.sh`（云端）** 一致；**Cortex 与 `vmcontrol` 在配置里常同为 19996**，同机勿混跑两进程占同一端口。

| 服务 | 默认端口 | 说明 |
|------|----------|------|
| Gateway | 19999 | HTTP API、`/internal`、lifespan 注册 Entangled schema 等 |
| Queue | 19997 | Task / Saga / Workers 侧 |
| File | 19995 | 文件服务（novaic-storage-a） |
| Cortex | 19996 | `CORTEX_PORT`；**无** `services.json` 的 `cortex` 键；Runtime 用 `NOVAIC_CORTEX_URL` |
| Entangled HTTP | 19900 | `entangled-service`；**`scripts/start.sh` 所列云端栈未必单独拉起该进程**，与「实体在 Entangled」的架构叙述需按环境区分（见 verification） |
| Tools Server | 19998 | **配置项仍在**；父仓未必部署；业务上多由 Runtime handlers + Cortex 替代 |
| LLM Factory | 视部署 | 生产常为独立主机/端口；本地示例可能为 9100 等，**以运行环境为准** |
| `tool_result_service`（若启用） | 19994 | `services.json` 仍有键；**未**列入上方「主栈」叙述，见 `ServiceConfig` |

**脚本差异**：`scripts/start-all.sh` / `novaic-app/scripts/start-backends.sh` 与云端 `start.sh` 在 **Queue / Cortex / Tools** 上可能不一致；联调以 **`docs/runbooks/E2E_READINESS.md`** + 实际脚本为准。**Entangled :19900** 在联调文档中常出现，但云端 **`scripts/start.sh` 未必单独拉起** `entangled-service`（与 §7、`architecture-verification` 一致）。

---

## 4. 数据归属（一句话）

| 数据类型 | 权威位置 | 备注 |
|----------|----------|------|
| 业务实体（agents、messages 等） | **Entangled** SQLite（服务端） | Gateway 经 client 访问；v63 后 Gateway 本地库大量业务表已迁出/影子表，见 verification |
| 对话与 Workspace 正文 | **Cortex**（S3） | scope / steps；非旧 RO `agent_runtimes` 模型 |
| 任务与 Saga 状态 | **Queue DB** | tasks / sagas |
| 运维与配置项 | Gateway `config` 等 | 随 verification |

---

## 5. 消息与 Agent 环路

**摘要**：用户发消息 → Gateway 侧 chat 流 → Watchdog / MessageProcess Saga → RuntimeStart → **ReactThink**（`cortex.prepare_llm_context` + LLM Factory + context.save）→ **ReactActions**（`tool_handlers` 统一 dispatch；**无独立 Tools Server 主线**）→ 回写消息 → Entangled 侧同步到客户端。

**存储权威（与 §4 一致）**：`messages` / `chat_messages` 等**业务实体行**以 **Entangled** 为权威；`MessageRepository` 经 Entangled 访问。流程叙述见 **`HANDOVER.md` §12.2 / §12.6**；表级真相见 **`architecture-verification-2026-04.md`** 与 **`novaic-gateway/gateway/db/schema.py`（v63）**。

**细节与数据库行**：只维护一份详述：**`HANDOVER.md` §十二**（含 12.4 工具链）。本指南不重复贴全流程 ASCII。

---

## 6. 同步与 Entangled（只记边界）

- **合约版本**：`syncContractVersion`，Gateway 与 Entangled `ws_handler` 应对齐；见 [`SYNC_CONTRACT.md`](SYNC_CONTRACT.md)。  
- **桌面实体同步**：**Entangled Service WebSocket**（`entangled_transport`），**不是** Gateway AppBridge 上的实体 sync 主通道；见 [`entangled-sync-protocol-v1.md`](entangled-sync-protocol-v1.md) §1、[`SYNC_CONTRACT.md`](SYNC_CONTRACT.md) §5–§6。  
- **执行清单**：[`sync-contract-execution-checklist.md`](sync-contract-execution-checklist.md)。

---

## 7. 部署与仓库操作（摘要）

- **统一部署 CLI**：根目录 `./deploy`（子命令含 `gateway`、`runtime`、`services`、`cortex`、`factory` 等；**无** `orchestrator`）。  
- **`./deploy services`**（或等价「全量后端同步」）：`deploy` 脚本会 rsync **`Entangled` 子模块**等（与 `architecture-verification` §1 一致）；**不等于**在目标机自动起满 §3 全部 HTTP 进程。  
- **`./deploy tools`**：仍可能 rsync `novaic-tools-server` 目录名；根目录无该目录时会失败 — 与「工具已分拆/退役」并存，运维需明确是否仍部署该分拆仓。  
- **云端后端启动**：典型见 `scripts/start.sh`（Gateway / Queue / File / Cortex + Workers；**不**含本文 §3 表中全部进程）。  

**更细的命令、域名、环境变量**：只维护一份详述：**`HANDOVER.md`**（避免与本页重复）。

---

## 8. 父仓与子模块文档

- `docs/submodules/**` **仅 README**：指向各子模块仓库；父仓**不**保留镜像正文。  
- 历史镜像：**`git show` / tag** 说明见 [`submodules/README.md`](submodules/README.md)（勿使用已失效路径；以该文为准）。  

---

## 9. 历史文档与 Graveyard

- `docs/_graveyard/`、`docs/archived/` 已从当前工作树删除；历史内容见 tag（如 **`docs-graveyard-p2`**）或旧提交。  
- `docs/vnc/`、`docs/review/`、`docs/misc/survey-2026/` 仅 **README 占位**。  
- **策略与清单**：[`DOCUMENT_AGGRESSIVE_STRATEGY.md`](DOCUMENT_AGGRESSIVE_STRATEGY.md)、[`DOCUMENT_INVENTORY.md`](DOCUMENT_INVENTORY.md)（自动生成）。  
- **全文持疑核验进度**：[`DOC_VERIFICATION_REGISTRY.md`](DOC_VERIFICATION_REGISTRY.md)（每文件一行；模板与脚本见该文）。

---

## 10. 推荐阅读顺序

| 读者 | 顺序 |
|------|------|
| **新人** | 本文件 → [`README.md`](README.md) → [`backend-architecture.md`](backend-architecture.md) → [`agent-handoff-context.md`](agent-handoff-context.md) → [`HANDOVER.md`](../HANDOVER.md) 目录与本地开发章节 |
| **对代码/部署较真** | [`architecture-verification-2026-04.md`](architecture-verification-2026-04.md) → 再读 HANDOVER 相关节 |
| **做同步/桌面缓存** | [`SYNC_CONTRACT.md`](SYNC_CONTRACT.md) → [`entangled-sync-protocol-v1.md`](entangled-sync-protocol-v1.md) → checklist |
| **做 Cortex/Scope** | [`cortex-architecture.md`](cortex-architecture.md) → [`context-assembly-dfs-step-tree.md`](context-assembly-dfs-step-tree.md) → [`scope-driven-agent-lifecycle.md`](scope-driven-agent-lifecycle.md)（**先读 §〇 与代码对照表**；实现以 `novaic-cortex` / `novaic-agent-runtime` 为准） |
| **联调** | [`runbooks/E2E_READINESS.md`](runbooks/E2E_READINESS.md)、[`runbooks/ARCHITECTURE-SERVICES-AND-HANDLERS.md`](runbooks/ARCHITECTURE-SERVICES-AND-HANDLERS.md) |

---

## 11. 附录：目录角色速查（避免重复打开错文件夹）

| 路径 | 角色 |
|------|------|
| `design/` | 迁移/方案草稿，**非**唯一真值 |
| `research/` | 调研与根因，时点记录 |
| `device/` | 设备域回合稿；现行实现以 app + Entangled 为准 |
| `gateway-upgrade/` | Gateway 拆分**过程**记录 |
| `ota/`、`p2p/` | 专题过程稿与修复记录 |
| `misc/` | 联调、运维、索引见 [`misc/README.md`](misc/README.md) |
| `agent-approve-points/` | 审核清单 |
| `_archive/`、`NEW_DOCUMENTATION_BLUEPRINT.md` | **文档快照说明**与**重建蓝图**（tag + 清单；不替代 L1 SSOT） |
| `runbooks/` | **现行运维**（E2E、服务矩阵、热更新）；见 [`runbooks/README.md`](runbooks/README.md) |
| `_legacy/` | **L3 档案角色说明**（不放正文）；见 [`_legacy/README.md`](_legacy/README.md) |

---

## 12. 修订说明

本页**不**替代 L1 各篇全文；新增内容时请先更新 **backend-architecture / verification / HANDOVER**，再收紧本页摘要，保持**单点摘要、多点详述**结构，以维持「全面、无冗余」。
