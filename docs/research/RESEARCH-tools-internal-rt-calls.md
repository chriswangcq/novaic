# 研究报告：Tools 对 /internal/rt/ 的调用

## 一、调用汇总

### 1.1 Tools Server task_queue/client.py（GatewayInternalClient）

| 方法 | 调用路径 | 目标 URL | 调用方 |
|------|----------|----------|--------|
| `get_quadrant_task_board(agent_id)` | `/internal/rt/{runtime_id}/quadrant-tasks/board` | **RO** (internal_url) | system_prompt |
| `get_growth_log(agent_id)` | `/internal/rt/{runtime_id}/self-drive/growth-log` | **RO** | **无** |
| `get_drive_config(agent_id)` | `/internal/rt/{runtime_id}/self-drive/config` | **RO** | **无** |
| `get_self_drive_state(agent_id)` | `/internal/rt/{runtime_id}/self-drive/state` | **RO** | **无** |

**说明**：`_request` 对 `/internal/*` 使用 `internal_url` = RUNTIME_ORCHESTRATOR_URL，故请求发往 **RO**，不经过 Gateway。

### 1.2 runtime_id 构造方式（问题）

```python
# client 内部构造
runtime_id = f"{agent_id}:{subagent.get('id', 'main')}:0"  # 例如 "ag-123:main:0"
# 或
runtime_id = f"{agent_id}:main:0"
```

**问题**：RO 的 `resolve_runtime_ids(runtime_id)` 期望 `rt-xxx` 格式，查 `agent_runtimes` 表。`ag-123:main:0` 非合法 runtime_id，**会 404**。当前逻辑依赖异常捕获和 fallback 默认值。

### 1.3 RO task_queue/client.py

与 Tools Server 相同 4 个方法，同样调用 `/internal/rt/*`，目标为 **RO 自身**（RO 的 internal router）。

---

## 二、Tools Server executor（工具执行）

**executor 不使用** `/internal/rt/`，全部使用 agent 维度：

| 工具类别 | 实际路径 | 目标 |
|----------|----------|------|
| memory_* | `/internal/agents/{agent_id}/memory/*` | Gateway |
| notebook_* | `/internal/agents/{agent_id}/notebook/*` | Gateway |
| task_* | `/internal/agents/{agent_id}/quadrant-tasks*` | Gateway |
| drive_log_growth | `/internal/agents/{agent_id}/growth-logs` | Gateway |
| goal_* | `/internal/agents/{agent_id}/memory/save` 等 | Gateway |

executor 的 `base_url` 为 `GATEWAY_URL`，故工具执行走 **Gateway**，不走 RO。

---

## 三、调用链分析

### 3.1 get_quadrant_task_board

```
system_prompt.build_system_prompt(agent_id, client)
  → main_subagent = client.get_main_subagent(agent_id)
  → runtime_id = main_subagent.get("runtime_id")   # 可能为 None
  → if runtime_id:
       client.get_quadrant_task_board(runtime_id)  # 传 runtime_id，但方法参数名为 agent_id
```

**问题**：
- `get_main_subagent` 返回的 subagent 通常**不含** `runtime_id`（Gateway 的 subagent 表无此字段）
- 即使有，`get_quadrant_task_board` 签名是 `(agent_id)`，内部会再构造 `runtime_id = f"{agent_id}:main:0"`
- 当传入 `runtime_id` 时，实际会构造 `f"{runtime_id}:main:0"`，格式错误

### 3.2 get_growth_log、get_drive_config、get_self_drive_state

**全仓库无调用方**，为死代码。

### 3.3 system_prompt 的 drive 数据来源

```python
drive = client.get_agent_drive(agent_id)  # GET /internal/agents/{agent_id}/drive
drive_config = drive.get("drive_config")
growth_log = drive.get("growth_log")
```

drive、drive_config、growth_log 均来自 `get_agent_drive`，即 `/internal/agents/{agent_id}/drive`，**不依赖** `get_growth_log`、`get_drive_config`。

---

## 四、RO runtime.py 的 /internal/rt/* 代理

RO 的 `runtime.py` 中有多处 `client.forward` 到 `/internal/rt/{runtime_id}/*`：

| 类别 | 路径示例 |
|------|----------|
| memory | `/internal/rt/{runtime_id}/memory/save`, recall, delete, namespaces, task/log, task/history |
| notebook | `/internal/rt/{runtime_id}/notebook/write`, read, list, update, delete |
| chat | `/internal/rt/{runtime_id}/chat/event`, history, message/{id} |
| qemu | `/internal/rt/{runtime_id}/qemu/ssh-exec`, status, start, shutdown, restart |
| tasks | `/internal/rt/{runtime_id}/tasks/spawn`, tasks |
| drive | `/internal/rt/{runtime_id}/drive`, drive/get, update-profile, update |

这些是 **RO 内部** 调用自身 internal router，用于 runtime 维度的 memory、notebook、chat 等。

**工具执行**：由 Tools Server executor 直接调用 Gateway 的 `/internal/agents/{agent_id}/*`，**不经过** RO 的 `/internal/rt/*`。

---

## 五、结论

### 5.1 Tools Server 对 /internal/rt/ 的调用

| 调用 | 目标 | 状态 |
|------|------|------|
| get_quadrant_task_board | RO | 可能 404（runtime_id 格式错误），有 fallback |
| get_growth_log | RO | 死代码，无调用方 |
| get_drive_config | RO | 死代码，无调用方 |
| get_self_drive_state | RO | 死代码，无调用方 |

### 5.2 工具执行路径

- **内置工具**（memory、notebook、task、drive 等）：executor → Gateway `/internal/agents/{agent_id}/*`
- **不经过** `/internal/rt/`

### 5.3 建议

1. **Tools Server client**：将 `get_quadrant_task_board` 改为调用 `/internal/agents/{agent_id}/quadrant-tasks/board`，与 executor 一致。
2. **删除死代码**：`get_growth_log`、`get_drive_config`、`get_self_drive_state` 可删除。
3. **system_prompt**：修正 `get_quadrant_task_board` 的入参，应传 `agent_id` 而非 `runtime_id`；若改用 agent 路由，则无需 runtime_id。
