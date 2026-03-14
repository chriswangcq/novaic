# RO 保留模块实际生效分析

> 分析 `gateway/api/internal/runtime.py`、`subagent.py`、`helpers.py` 中各路由/函数的实际调用方与生效情况。
> **2025-03 已执行删除**：本文档中标记为「可删」的路由已移除。

---

## 一、调用方总览

| 调用方 | 目标 | 说明 |
|--------|------|------|
| **agent-runtime ro_client** | RO (19993) | 直接调用，用于 runtime/subagent 编排、HRL、drive 等 |
| **agent-runtime gateway_client** | Gateway (19999) | 用于 messages、subagent 状态(awake/sleeping/completed)、due-wake 等 |
| **Gateway client.forward()** | RO (19993) | 出站调用 runtimes/latest、cancel-by-subagent、delete-by-subagent |
| **Tools Server** | Gateway (19999) | 使用 subagents/list、with-tools、history、send、rest、tool-context、tool-ports |

**结论**：Tools Server 只调 Gateway，不直接调 RO。agent-runtime 的 subagent 状态变更（awake/sleeping/completed）走 Gateway，不走 RO。

---

## 二、runtime.py 路由生效情况

### 2.1 实际生效（agent-runtime ro_client 或 Gateway forward）

| 路由 | 方法 | 调用方 | 说明 |
|------|------|--------|------|
| `/runtimes/{runtime_id}` | GET | ro_client.get_runtime | ✓ |
| `/runtimes` | POST | ro_client.create_runtime | ✓ |
| `/runtimes/get-or-create` | POST | ro_client.get_or_create_runtime | ✓ |
| `/runtimes/{id}` | PATCH | ro_client.update_runtime | ✓ |
| `/runtimes/{id}/advance` | POST | ro_client.advance_round | ✓ |
| `/runtimes/{id}/context/append` | POST | ro_client.append_context | ✓ |
| `/runtimes/{id}/set-status` | POST | ro_client.set_runtime_status | ✓ |
| `/runtimes/{id}/summarized` | POST | ro_client.set_runtime_summarized | ✓ |
| `/runtimes/{id}/hot-cold-summary` | POST | ro_client.set_runtime_hot_cold_summary | ✓ |
| `/runtimes/{id}/need-rest` | POST | ro_client.set_runtime_need_rest | ✓ |
| `/runtimes/subagent/{agent_id}/{subagent_id}` | GET | ro_client.get_subagent_runtime | ✓ |
| `/runtimes/batch` | POST | ro_client.get_runtimes_by_ids | ✓ |
| `/runtimes/cancel-by-subagent` | POST | Gateway client.forward | ✓ |
| `/runtimes/delete-by-subagent` | POST | Gateway client.forward | ✓ |
| `/runtimes/latest/{agent_id}/{subagent_id}` | GET | Gateway client.forward | ✓（用于解析 runtime_id） |

### 2.2 可能未生效（无明确调用方）

| 路由 | 方法 | 说明 |
|------|------|------|
| `/runtimes/active` | GET | 无 ro_client 方法；Tools Server 用 subagents/list |
| `/runtimes/list` | GET | 文档称 Tools Server 用，但 Tools Server 实际用 Gateway `/internal/subagents/list` |
| `/runtimes/with-tools` | GET | Tools Server 用 Gateway `/internal/subagents/with-tools` |
| `/runtimes/main` | POST | 无 ro_client 对应方法 |
| `/runtimes/main/{agent_id}` | GET | ro_client 用 subagents/main，非此路由 |
| `/runtimes/{id}/wake` | POST | 无 ro_client 方法；contract 测试有，但生产调用链未找到 |
| `/runtimes/{id}/tool-ports` | POST | Tools Server 用 Gateway `/internal/subagents/{id}/tool-ports` |
| `/runtimes/{id}` | DELETE | 无 ro_client 方法 |
| `/agents/{agent_id}/subagents/{subagent_id}/has-active-runtime` | GET | 无调用方 |
| `/runtimes/{id}/history` | POST | 无 ro_client；Tools Server 用 subagents/history |
| `/runtimes/{id}/send` | POST | 无 ro_client；Tools Server 用 subagents/send |

---

## 三、subagent.py 路由生效情况

### 3.1 实际生效（agent-runtime ro_client）

| 路由 | 方法 | 调用方 | 说明 |
|------|------|--------|------|
| `/subagents/{agent_id}/main` | GET | ro_client.get_main_subagent | ✓ |
| `/subagents/{agent_id}/{subagent_id}` | GET | ro_client.get_subagent | ✓ |
| `/subagents/{agent_id}/{subagent_id}/status` | GET | ro_client.get_subagent_status | ✓ |
| `/subagents/{agent_id}/{subagent_id}/hrl` | GET | ro_client.get_hrl | ✓ |
| `/subagents/{agent_id}/{subagent_id}/hrl/add` | POST | ro_client.add_to_hrl | ✓ |
| `/subagents/{agent_id}/{subagent_id}/summary-lock` | GET | ro_client.get_summary_lock | ✓ |
| `.../summary-lock/acquire` | POST | ro_client.acquire_summary_lock | ✓ |
| `.../summary-lock/release` | POST | ro_client.release_summary_lock | ✓ |
| `.../merge-history` | POST | ro_client.atomic_merge_history | ✓ |
| `/agents/{agent_id}/drive` | GET | ro_client.get_agent_drive | ✓ |
| `/agents/{agent_id}/notebook-summary` | GET | ro_client.get_notebook_summary | ✓ |
| `/agents/{agent_id}/drive/increment-interaction` | POST | ro_client.increment_drive_interaction | ✓ |
| `/agents/{agent_id}/info` | GET | ro_client.get_agent_info | ✓ |

### 3.2 可能未生效（agent-runtime 走 Gateway 或无调用方）

| 路由 | 方法 | 说明 |
|------|------|------|
| `/subagents/due-wake` | GET | agent-runtime 用 gateway_client → Gateway |
| `/subagents/{agent_id}/{subagent_id}/sleeping` | POST | agent-runtime 用 gateway_client → Gateway |
| `/subagents/{agent_id}/{subagent_id}/awake` | POST | 同上 |
| `/subagents/{agent_id}/{subagent_id}/summarizing` | POST | 同上 |
| `/subagents/{agent_id}/{subagent_id}/completed` | POST | 同上 |
| `/subagents/{agent_id}/{subagent_id}/failed` | POST | 同上 |
| `/subagents/{agent_id}/{subagent_id}` | PATCH | ro_client 无 update_subagent；Gateway 有 PATCH |
| `/subagents/{agent_id}/spawn` | POST | Gateway 实现 spawn 本地，仅 forward runtimes/latest 到 RO |
| `/subagents/{agent_id}/{subagent_id}/cancel` | POST | Gateway 实现后 forward cancel-by-subagent 到 RO |
| `/subagents/{agent_id}/{subagent_id}` | DELETE | 无调用方 |

---

## 四、helpers.py 函数生效情况

| 函数 | 说明 |
|------|------|
| `resolve_agent_id_from_subagent` | 依赖 `gateway.clients.runtime_orchestrator`，RO 进程内可能未使用（Gateway 用于解析 subagent_id） |
| `resolve_runtime_ids` | 被 runtime/subagent 路由内部使用 |
| `get_runtime_context` | 被路由内部使用 |
| `_runtime_to_dict` / `_subagent_to_dict` | 序列化辅助 |
| `set_runtime_orchestrator_process` | RO 启动时设为 True，避免自代理 |
| `maybe_forward_to_runtime_orchestrator` | **RO 进程内恒返回 None**（死代码分支），仅 Gateway 进程会 forward |

---

## 五、汇总：实际生效 vs 可考虑删除

### 5.1 实际生效路由（约 23 个）

**runtime.py**：get, post, get-or-create, patch, advance, context/append, set-status, summarized, hot-cold-summary, need-rest, subagent, batch, cancel-by-subagent, delete-by-subagent, latest

**subagent.py**：main, get, status, hrl, hrl/add, summary-lock×3, merge-history, agents/drive, notebook-summary, increment-interaction, info

### 5.2 可能未生效（可考虑删除或标记废弃）

| 模块 | 路由/功能 | 建议 |
|------|-----------|------|
| runtime.py | runtimes/active | 无调用方，可删 |
| runtime.py | runtimes/list | Tools Server 用 subagents/list，可删 |
| runtime.py | runtimes/with-tools | Tools Server 用 subagents/with-tools，可删 |
| runtime.py | runtimes/main (POST), runtimes/main/{agent_id} (GET) | 无 ro_client，可核实后删 |
| runtime.py | runtimes/{id}/wake | contract 有，生产链未找到，保留或标记 |
| runtime.py | runtimes/{id}/tool-ports | Tools Server 用 subagents，可删 |
| runtime.py | runtimes/{id} DELETE | 无调用方，可删 |
| runtime.py | has-active-runtime | 无调用方，可删 |
| runtime.py | runtimes/{id}/history | 无调用方，可删 |
| runtime.py | runtimes/{id}/send | 无调用方，可删 |
| subagent.py | due-wake | agent-runtime 走 Gateway，RO 实现可能冗余 |
| subagent.py | sleeping, awake, summarizing, completed, failed | agent-runtime 走 Gateway，RO 实现可能冗余 |
| subagent.py | spawn | Gateway 本地实现，RO 可能无入站调用 |
| subagent.py | cancel | Gateway forward 到 cancel-by-subagent，RO 的 cancel 路由可能未被直接调用 |
| subagent.py | DELETE subagent | 无调用方，可删 |
| helpers.py | maybe_forward_to_runtime_orchestrator | RO 内恒返回 None，分支为死代码 |

### 5.3 需进一步核实

- **runtimes/main**：ro_client.get_main_subagent 调用的是 `GET /internal/subagents/{agent_id}/main`，不是 runtimes/main。runtimes/main 可能未被使用。
- **due-wake**：scheduler 用 gateway_client.get_due_for_wake → Gateway。RO 的 due-wake 是否被调用取决于部署拓扑（若 Gateway 转发 subagents 到 RO 则可能用到）。
- **runtimes/{id}/wake**：contract 测试与脚本有使用，需确认生产是否依赖。

---

## 六、结论

- **实际生效**：约 **23 个** 路由/端点被 agent-runtime ro_client 或 Gateway forward 使用。
- **可能未生效**：约 **16+** 个路由/分支无明确调用方或与 Gateway 重叠，可评估后删除或标记废弃。
- **maybe_forward_to_runtime_orchestrator**：在 RO 进程内为死代码（恒返回 None），仅 Gateway 进程会执行 forward 逻辑。
