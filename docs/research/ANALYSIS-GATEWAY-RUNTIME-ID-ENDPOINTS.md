# 分析：Gateway 中 runtime_id 相关端点的用途与可删性

## 一、各模块调用情况

### 1. config.py

| 端点 | 用途 | 依赖 | 调用方 | 结论 |
|------|------|------|--------|------|
| `GET /config/llm/runtime/{runtime_id}` | 根据 runtime_id 解析 agent_id，返回该 agent 的 LLM 配置 | `get_runtime_context` | llm_handlers（agent-runtime、tools-server）发往 gateway_url | **会 404**：Gateway agent_runtimes 空 |

### 2. task.py

| 端点 | 用途 | 依赖 | 调用方 | 结论 |
|------|------|------|--------|------|
| `POST/GET/PATCH... /rt/{runtime_id}/quadrant-tasks/*` | 四象限任务 CRUD，用 runtime_id 解析 agent_id | `resolve_runtime_ids` | **无**：Tools Server 已改用 `/internal/agents/{agent_id}/quadrant-tasks` | **可删** |
| `POST /rt/{runtime_id}/growth-logs` | 成长日志 | `resolve_runtime_ids` | **无**：Tools Server 用 `/internal/agents/{agent_id}/growth-logs` | **可删** |

task.py 另有 agent 维度 API：`/agents/{agent_id}/quadrant-tasks`，**有人用**，保留。

### 3. self_drive.py

| 端点 | 用途 | 依赖 | 调用方 | 结论 |
|------|------|------|--------|------|
| `GET /rt/{runtime_id}/self-drive/state` | 自驱状态 | `resolve_runtime_ids` | **无**：Tools Server 已删 get_self_drive_state | **可删** |
| `GET /rt/{runtime_id}/self-drive/config` | 自驱配置 | `resolve_runtime_ids` | **无**：Tools Server 已删 get_drive_config | **可删** |
| `PATCH /rt/{runtime_id}/self-drive/config` | 更新自驱配置 | `resolve_runtime_ids` | **无** | **可删** |
| `GET /rt/{runtime_id}/self-drive/profile-assessment` | 画像评估 | `resolve_runtime_ids` | **无** | **可删** |
| `GET /rt/{runtime_id}/self-drive/task-suggestions` | 任务建议 | `resolve_runtime_ids` | **无** | **可删** |
| `GET/POST /rt/{runtime_id}/self-drive/growth-log` | 成长日志 | `resolve_runtime_ids` | **无**：Tools Server 已删 get_growth_log | **可删** |

**self_drive.py 全部为 runtime_id 端点，无人调用，整模块可删。**

### 4. llm.py

| 端点 | 用途 | 依赖 | 结论 |
|------|------|------|------|
| `POST /debug/llm/call` | 调试 LLM | 无 | 保留 |
| `POST /llm/compact-context` | 上下文压缩 | 无 | 保留 |

**llm.py 仅 import 了 resolve_runtime_ids、get_runtime_context，未使用，可删 import。**

### 5. agent.py

| 用途 | 依赖 | 说明 |
|------|------|------|
| subagent/spawn、status、cancel 等 | `client.forward` 到 RO 的 `/internal/runtimes/latest/...` | 不查 agent_runtimes，是 Gateway 主动调 RO |
| 其他 agent 维度 API | 无 | 用 agent_id，不依赖 resolve |

**agent.py 的 resolve_runtime_ids、get_runtime_context 为 import 未用，可删 import。**（需再确认是否有实际调用）

### 6. subagent.py

| 用途 | 依赖 | 结论 |
|------|------|------|
| `/status` 的 `runtime_repo.get_latest_runtimes` | RuntimeRepository | **无效**：表空，恒返回 [] |
| hrl/add 的 `runtime_id` | body 参数，仅写入 subagents.hrl | 不查 agent_runtimes |

**可删**：`/status` 中的 get_latest_runtimes 分支。

### 7. message.py

**仅 import，未使用 resolve_runtime_ids、get_runtime_context。可删 import。**

### 8. health.py、broadcast.py、web.py

**仅 import，未使用。可删 import。**

---

## 二、调用方汇总

| 调用方 | 目标 | 实际路径 |
|--------|------|----------|
| **Tools Server executor** | 四象限、memory、chat、qemu、growth-logs 等 | `/internal/agents/{agent_id}/*`（agent 维度） |
| **Tools Server client** | 四象限看板 | `/internal/agents/{agent_id}/quadrant-tasks/board` |
| **agent-runtime llm_handlers** | LLM 配置 | `GET /internal/config/llm/runtime/{runtime_id}` → 发往 **gateway_url** |
| **agent-runtime** 其他 runtime 请求 | get_runtime、append_context 等 | 发往 **internal_url (RO)** |

---

## 三、可删除项清单

### 3.1 整模块删除

| 模块 | 原因 |
|------|------|
| **self_drive.py** | 全部为 `/rt/{runtime_id}/self-drive/*`，无人调用 |

### 3.2 删除路由（保留 agent 维度）

| 文件 | 删除内容 |
|------|----------|
| **task.py** | 所有 `/rt/{runtime_id}/quadrant-tasks/*`、`/rt/{runtime_id}/growth-logs` 路由 |
| **config.py** | `GET /config/llm/runtime/{runtime_id}`（或改为转发到 RO） |

### 3.3 删除无效逻辑

| 文件 | 删除内容 |
|------|----------|
| **subagent.py** | `/status` 中的 `get_latest_runtimes` 分支 |
| **message.py** | INTERRUPT 中的 `UPDATE agent_runtimes` |

### 3.4 删除无用 import

| 文件 | 删除 import |
|------|-------------|
| llm.py | resolve_runtime_ids, get_runtime_context, _runtime_to_dict, _subagent_to_dict |
| message.py | resolve_runtime_ids, get_runtime_context |
| health.py | resolve_runtime_ids, get_runtime_context, _runtime_to_dict, _subagent_to_dict |
| broadcast.py | 同上 |
| web.py | 同上 |
| agent.py | 需确认是否使用 |

### 3.5 删除 helpers 与 Repository

完成上述删除后，若无其他引用：

- 可删 `helpers.py` 中的 `resolve_runtime_ids`、`get_runtime_context`
- 可删 `RuntimeRepository`、`agent_runtimes` 表相关逻辑（或保留表结构做迁移兼容）

---

## 四、config/llm/runtime 的特殊处理

`GET /internal/config/llm/runtime/{runtime_id}` 被 llm_handlers 调用，发往 gateway_url。

- **现状**：Gateway agent_runtimes 空 → 404
- **可选方案**：
  1. **方案 A**：llm_handlers 改为调用 RO（internal_url）的该接口
  2. **方案 B**：Gateway 将该请求转发到 RO
  3. **方案 C**：改为 agent 维度，llm_handlers 传 agent_id，调用 `/config/llm/agent/{agent_id}`（若已有）

---

## 五、总结

| 类型 | 数量 | 说明 |
|------|------|------|
| **整模块可删** | 1 | self_drive.py |
| **路由可删** | ~15 | task.py 的 /rt/quadrant-tasks、growth-logs；config 的 llm/runtime |
| **逻辑可删** | 2 | subagent /status 的 get_latest_runtimes；message INTERRUPT 的 UPDATE |
| **import 可删** | 5+ | llm, message, health, broadcast, web |
| **需改造** | 1 | config/llm/runtime 的调用链或转发 |

删除后，Gateway 将不再依赖 `resolve_runtime_ids`、`get_runtime_context`、`RuntimeRepository`、`agent_runtimes`。
