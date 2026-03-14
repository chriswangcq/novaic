# Split Repos 重复代码盘点

> 生成时间: 2026-03-03

## 一、已共享的模块 (novaic-shared-runtime-common)

以下模块已抽到 `novaic-shared-runtime-common`，各 repo 通过 `from shared_runtime_common import ...` 使用：


| 模块                               | 使用方                                               | 说明                                            |
| -------------------------------- | ------------------------------------------------- | --------------------------------------------- |
| `common.db`                      | agent-runtime, tools-server, runtime-orchestrator | Database, DatabaseLockManager, FIFOLock       |
| `common.enums`                   | agent-runtime, tools-server, runtime-orchestrator | RuntimeStatus, SubagentStatus                 |
| `common.exceptions`              | agent-runtime, tools-server, runtime-orchestrator | BusinessError, ValidationError, NotFoundError |
| `common.utils.time`              | agent-runtime, tools-server, runtime-orchestrator | utc_now, parse_iso, humanize_duration         |
| `common.utils.image_storage`     | agent-runtime, tools-server, runtime-orchestrator | ImageStorage, get_image_storage               |
| `common.tools`                   | agent-runtime, tools-server, runtime-orchestrator | BUILTIN_TOOLS, VM_TOOLS                       |
| `task_queue.constants`           | agent-runtime                                     | PHASE_NEED_THINK, PHASE_COMPLETED             |
| `task_queue.exceptions`          | agent-runtime                                     | PayloadValidationError, BusinessError         |
| `task_queue.heartbeat_sync`      | agent-runtime                                     | HeartbeatSync, heartbeat_sync                 |
| `task_queue.utils.broadcast`     | agent_runtime                                     | BroadcastType, sync_broadcast_log             |
| `task_queue.handlers.validation` | agent-runtime                                     | validate_payload                              |
| `service_runtime`                | gateway                                           | build_health_payload, resolve_bind            |


**各 repo 的 `common/` 目录**：多为薄包装，仅 `from shared_runtime_common.common.xxx import ...` 再导出。

---

## 二、完全重复（identical）的代码


| 路径                       | 涉及 Repo                                                                | 说明                   |
| ------------------------ | ---------------------------------------------------------------------- | -------------------- |
| `mcp_client/`            | novaic-tools-server                                                    | **已优化**：RO 已移除 mcp_client，仅保留 `skills/` 目录 |
| `common/http/clients.py` | novaic-agent-runtime, novaic-tools-server, novaic-runtime-orchestrator, **novaic-gateway** | **100% 相同**（4 个 repo，42 行/份） |


**建议**：将 `mcp_client` 和 `common/http/clients.py` 抽到 `novaic-shared-runtime-common` 或新建 `novaic-shared-mcp`。

---

## 三、高度相似（需人工合并）的代码

### 3.1 gateway/api/internal/ (Gateway vs Runtime-Orchestrator)


| 文件            | Gateway | RO    | 差异说明                                                                  |
| ------------- | ------- | ----- | --------------------------------------------------------------------- |
| `helpers.py`  | 有       | 有     | 实现不同，RO 的 helpers 更精简                                                 |
| `subagent.py` | 868 行   | 299 行 | Gateway 含更多路由（list_subagents 等），RO 仅保留 get_main/get_subagent/status 等 |
| `__init__.py` | 有       | 有     | 路由注册不同                                                                |


**说明**：这些文件由 `split_internal_api.py` 自动生成，Gateway 与 RO 职责不同，部分路由 Gateway 代理到 RO，部分 Gateway 自处理。属于**有意分叉**，非简单重复。

### 3.2 gateway/db/ (Gateway vs Runtime-Orchestrator)


| 文件                  | 差异                                                                                                |
| ------------------- | ------------------------------------------------------------------------------------------------- |
| `schema.py`         | Gateway 1468 行 vs RO 1434 行，表结构有分叉（RO 有 runtime 相关，Gateway 有 subagent_context 等）                  |
| `migration.py`      | 迁移逻辑不同                                                                                            |
| `repositories/*.py` | agent, chat, config, drive, memory, session, subagent 均不同；Gateway 有 subagent_context，RO 有 runtime |
| `fix_indexes.sql`   | 不同                                                                                                |


**说明**：Gateway 与 RO 使用不同 DB 文件（gateway.db vs runtime_orchestrator.db），schema 和 repo 有意分叉，属于**架构设计**，非可合并重复。

### 3.3 gateway/clients/ (Gateway vs Runtime-Orchestrator)

| 文件                  | 差异                                                                 |
| -------------------- | -------------------------------------------------------------------- |
| `vmuse_adapter.py`   | **100% 相同**                                                        |
| `runtime_orchestrator.py` | **100% 相同**                                                   |
| `vmcontrol.py`       | **99% 相同**，仅 health 探测顺序不同（Gateway 多 `/`，RO 仅 `/health`、`/api/health`） |

**说明**：Gateway 与 RO 均需调用 vmcontrol、vmuse、runtime_orchestrator，可考虑抽到 shared 或由一方依赖另一方。

---

## 四、task_queue 相关（BACKLOG 已记录）


| 模块                                 | 位置                         | 说明                                            |
| ---------------------------------- | -------------------------- | --------------------------------------------- |
| `task_queue/`                      | **仅 novaic-agent-runtime** | 完整实现（client, handlers, sagas, workers, utils） |
| tools-server, runtime-orchestrator | 无 task_queue               | 不直接使用 task queue                              |


**BACKLOG 提及**：agent-runtime、tools-server、runtime-orchestrator 中的 `task_queue/client.py`、`utils/`、`business/` 等重复，建议抽到 shared 或新建 `novaic-shared-task-queue`。  
**现状**：task_queue 仅在 agent-runtime 中，tools-server 和 runtime-orchestrator 通过 HTTP 调用 queue-service，无本地 task_queue 代码。**无跨 repo 重复**。

---

## 五、storage-a vs storage-b


| 对比项  | 结论                                                          |
| ---- | ----------------------------------------------------------- |
| 核心逻辑 | 不同：storage-a 为 file_service，storage-b 为 tool_result_service |
| 共享部分 | 可能有 config、contract 等，需进一步比对                                |
| 脚本   | 各自独立（smoke_*.sh, backup, restore, verify_contract）          |


**说明**：两者为不同服务，非重复代码场景。

---

## 六、common/ 薄包装（re-export）

以下为各 repo 中 `common/` 下的薄包装，仅做 `from shared_runtime_common import ...`：

- `novaic-agent-runtime/common/{db,enums,exceptions,utils,utils/time,utils/image_storage,tools}`
- `novaic-tools-server/common/{db,enums,exceptions,utils,utils/time,utils/image_storage,tools}`
- `novaic-runtime-orchestrator/common/{db,enums,exceptions,utils,utils/time,utils/image_storage,tools}`

**建议**：可考虑直接 `from shared_runtime_common`，减少一层包装；或保留以兼容现有 import 路径。

---

## 七、汇总与建议

### mcp_client 使用确认（2026-03-03）

| Repo | 使用情况 |
|------|----------|
| **novaic-tools-server** | **在用**：`MCPServerConnection`（executor 外部 MCP 调用）、`ToolRegistry`（tool_context_manager 发现 SubAgent MCP 工具）、`mcp_client/skills/`（api.py 列出 skills） |
| **novaic-runtime-orchestrator** | **已优化**：已移除 mcp_client Python 包，仅保留 `skills/` 目录（skill.py 加载 SKILL.md） |
| **novaic-gateway** | **未用**：无 mcp_client 目录，skill.py 的 `_find_builtin_skills_dir` 返回 None |

**结论**：mcp_client 在 tools-server 中**在用**；RO 已优化，仅保留 `skills/` 目录，Python 包已移除。

### 高优先级（可立即去重）

1. **common/http/clients.py**：3 个 LIVE 副本（agent-runtime、tools-server、gateway）→ 抽到 `novaic-shared-runtime-common`；RO 副本为死代码，可删除
2. **RO 死代码清理**：删除 RO 的 `common/http/clients`、`gateway/clients/*`、`skills/`、`gateway/db/repositories/skill.py` 等（见 §10.4）

### 中优先级（待评估）

1. **common/ 薄包装**：评估是否统一改为直接 import shared，减少维护成本
2. **gateway/db**：Gateway 与 RO 的 schema/repo 分叉属架构设计，可考虑提取公共 migration 工具或 SQL 片段
3. **gateway/clients**：仅 Gateway 需要 vmcontrol、runtime_orchestrator；RO 副本为死代码；vmuse_adapter 两端皆死 → 无需共享，仅做 RO 清理
4. **skills/**：仅 tools-server 需要；RO 副本为死代码 → 无需共享，仅做 RO 清理
5. **mcp_client**：仅 tools-server 使用 → 可考虑抽到 shared（非去重刚需）

### 低优先级（已记录）

1. **task_queue**：BACKLOG 已记录，当前仅 agent-runtime 拥有，无跨 repo 重复
2. **gateway/api/internal**：由 split_internal_api 生成，属有意分叉，保持现状

---

## 八、文件统计


| Repo                        | gateway/ | common/ | task_queue/ | mcp_client/ |
| --------------------------- | -------- | ------- | ----------- | ----------- |
| novaic-gateway              | 67 个 .py | 17      | -           | -           |
| novaic-runtime-orchestrator | 49       | 12      | -           | 无（仅 skills/） |
| novaic-tools-server         | -        | 13      | -           | 有           |
| novaic-agent-runtime        | -        | 14      | 62          | -           |

---

## 九、深化分析（2026-03-03）

### 9.1 common/http/clients.py 抽到 shared 的可行性

| 依赖项 | 说明 |
|--------|------|
| `common.config.ServiceConfig` | 各 repo 均有 `common.config`，且 `INTERNAL_HTTP_TRUST_ENV` 定义一致 |
| 抽到 shared 方案 | 需 shared 提供 `get_internal_trust_env() -> bool` 或由各 repo 的 config 注入；或 shared 的 clients 接受 `trust_env: bool` 参数 |

**结论**：可抽到 shared，需在 shared 中定义 `create_internal_client(trust_env: bool, **kwargs)` 工厂，或由各 repo 的 config 模块提供 `INTERNAL_HTTP_TRUST_ENV` 供 shared 使用。

### 9.2 skills/ 目录重复

| 位置 | 说明 |
|------|------|
| `novaic-runtime-orchestrator/skills/` | 10 个 skill（agent-bootstrap, browser, context, desktop, files, shell, software, vm-setup, wechat, windows） |
| `novaic-tools-server/mcp_client/skills/` | **内容与 RO 完全一致**（`diff -rq` 无差异） |

**建议**：可考虑将 skills 抽到 `novaic-shared-runtime-common` 或新建 `novaic-shared-skills`，RO 与 tools-server 均从 shared 读取；或通过 CI 同步（RO 为 source of truth，tools-server 定期 copy）。

### 9.3 novaic-shared-kernel 与 common/http/clients

| 位置 | 说明 |
|------|------|
| `novaic-shared-kernel/src/common/http/clients.py` | 28 行，逻辑与各 repo 的 42 行版本一致，仅 docstring 更精简 |
| 各 repo 的 `common/http/clients.py` | 42 行，含 docstring |

**说明**：shared-kernel 已有 clients 实现，可评估是否统一迁移到 shared-kernel 或 shared-runtime-common。

---

## 十、死代码 vs 真正需共享（2026-03-03）

> 由 5 名 subagent 分别分析 RO、Gateway、tools-server、agent-runtime 的挂载与调用链，结论如下。

### 10.1 结论总表

| 重复项 | agent-runtime | tools-server | RO | gateway | 活副本数 | 死副本 |  verdict |
|--------|---------------|--------------|-----|---------|----------|--------|----------|
| **common/http/clients.py** | ✅ LIVE | ✅ LIVE | ❌ DEAD | ✅ LIVE | 3 | RO | **需共享**（3 个 repo） |
| **gateway/clients/vmcontrol** | - | - | ❌ DEAD | ✅ LIVE | 1 | RO | **仅 Gateway 需要** |
| **gateway/clients/runtime_orchestrator** | - | - | ❌ DEAD | ✅ LIVE | 1 | RO | **仅 Gateway 需要** |
| **gateway/clients/vmuse_adapter** | - | - | ❌ DEAD | ❌ DEAD | 0 | 两者 | **两者皆死** |
| **skills/** | - | ✅ LIVE | ❌ DEAD | - | 1 | RO | **仅 tools-server 需要** |
| **mcp_client** | - | ✅ LIVE | 已移除 | - | 1 | - | 无重复 |

### 10.2 详细说明

#### common/http/clients.py

| Repo | 使用位置 | 挂载/可达 | 结论 |
|------|----------|-----------|------|
| **agent-runtime** | task_queue/business/mcp, handlers/llm, summary, workers/health, utils/trs_sdk | ✅ task_queue 活跃 | **LIVE** |
| **tools-server** | executor, trs, api, tool_context_manager, tool_result_adapter | ✅ 均挂载/使用 | **LIVE** |
| **gateway** | agents, vm, routes, devices, runtime_orchestrator_forward, gateway/clients | ✅ 均挂载 | **LIVE** |
| **runtime-orchestrator** | helpers.resolve_agent_id（从未调用）、gateway/clients | ❌ 调用方均未挂载 | **DEAD** |

**结论**：RO 的 common/http/clients 可删除；agent-runtime、tools-server、gateway 需抽到 shared。

#### gateway/clients (Gateway vs RO)

| Client | Gateway | RO |
|--------|---------|-----|
| **vmcontrol** | routes, vm, vmcontrol, devices 均挂载 | **未挂载**（vm.py、vmcontrol.py 不在 RO app 中） |
| **runtime_orchestrator** | internal/subagent, agent, forward 均挂载 | **未挂载**（resolve_agent_id 从未调用） |
| **vmuse_adapter** | 仅 tests + example | 仅 example |

**结论**：RO 的 gateway/clients 可全部删除；Gateway 保留 vmcontrol、runtime_orchestrator；vmuse_adapter 两端皆死，可考虑移除。

#### skills/

| 位置 | 使用方 | 挂载 |
|------|--------|------|
| **RO skills/** | SkillRepository → skill.py | **skill.py 未挂载**，SkillRepository 从未被使用 |
| **tools-server mcp_client/skills/** | api.py `_list_skills()`, `_get_skill_content()` | internal_router `/subagents/.../skills` **已挂载** |

**结论**：RO 的 skills/ 及 SkillRepository 可删除；仅 tools-server 需要 skills 目录。

### 10.3 RO 挂载结构（仅 2 个 router）

```
app (main_runtime_orchestrator.py)
└── include_router(internal_router)  [prefix=/internal]
    ├── runtime_router   → /internal/runtimes/*, /internal/subagents/by-id/*
    └── subagent_router  → /internal/subagents/*, /internal/agents/*
+ app.get("/api/health")
```

**未挂载（死代码）**：routes.py, agents.py, vm.py, skills.py, devices.py, vmcontrol.py, chat_service.py, internal_proxy.py 等。

### 10.4 建议清理动作

| 动作 | 目标 |
|------|------|
| **RO 删除** | `common/http/clients.py`、`common/http/`、`gateway/clients/vmcontrol.py`、`gateway/clients/vmuse_adapter.py`、`gateway/clients/runtime_orchestrator.py`、`skills/`、`gateway/db/repositories/skill.py` 等（见 novaic-runtime-orchestrator/docs/DEAD_VS_LIVE_CODE_ANALYSIS.md） |
| **Gateway 删除** | `gateway/api/internal/web.py`、`gateway/api/internal/llm.py`、`gateway/api/internal/broadcast.py`、`gateway/clients/vmuse_adapter.py`（可选） |
| **抽到 shared** | `common/http/clients.py` → agent-runtime、tools-server、gateway 从 shared 消费 |

### 10.5 相关文档

- `novaic-runtime-orchestrator/docs/DEAD_VS_LIVE_CODE_ANALYSIS.md` – RO 死代码明细
- `docs/DUPLICATION_DEAD_VS_LIVE_ANALYSIS.md` – 跨 repo 死 vs 活结论
- `docs/COMMON_HTTP_CLIENTS_ANALYSIS.md` – common.http.clients 调用链
- **`docs/OPTIMIZATION_PLAN.md`** – 优化方案（分阶段执行步骤、删除清单、验证方法）


