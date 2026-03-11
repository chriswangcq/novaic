# SubAgent Agent 路由改造设计

## 一、背景与目标

### 1.1 问题
- Tools Server 调用 `POST /internal/agents/{agent_id}/subagent/spawn` 等 agent 路由
- Gateway 仅提供 `POST /internal/rt/{runtime_id}/subagent/spawn` 等 rt 路由
- 导致 subagent_spawn 返回 404

### 1.2 目标
- Gateway 提供正确的 agent 路由：`/internal/agents/{agent_id}/subagent/*`
- Gateway 不再提供 subagent 相关的 rt 路由（统一使用 agent 路由）

---

## 二、涉及模块与改动清单

| 模块 | 文件 | 改动类型 |
|------|------|----------|
| Gateway | `gateway/api/internal/agent.py` | 新增 4 个 agent 路由 |
| Gateway | `gateway/api/internal/runtime.py` | 删除 4 个 rt subagent 路由 |
| RO | `gateway/api/internal/agent.py` | 新增 4 个 agent 路由（与 Gateway 同步） |
| RO | `gateway/api/internal/runtime.py` | 删除 4 个 rt subagent 路由 |
| Tools Server | `tools_server/executor.py` | spawn/report 请求 body 增加字段 |

---

## 三、详细改动设计

### 3.1 Gateway - agent.py 新增 Agent 路由

**位置**：`novaic-gateway/gateway/api/internal/agent.py`  
**在 QEMU APIs 区块之后**（约第 470 行后）新增 SubAgent 区块。

#### 3.1.1 `POST /agents/{agent_id}/subagent/spawn`

**请求体**：
```json
{
  "task": "string",           // 必填
  "parent_subagent_id": "string",  // 必填，调用者 subagent_id（main 或 sub-xxx）
  "share_context": false,     // 可选，默认 false
  "timeout_minutes": 30       // 可选，默认 30
}
```

**逻辑**（复用 rt_subagent_spawn 核心逻辑，仅参数来源不同）：
1. 从 body 取 `parent_subagent_id`（必填，缺则 400）
2. `agent_id` 来自 URL
3. 创建 sub-subagent：`subagent_repo.create_sub_subagent(agent_id, parent_subagent_id, ...)`
4. share_context 时：`runtime_repo.get_active_runtime(parent_subagent_id, agent_id)` 取 parent 的 active runtime，取其 `context`
5. 写入 SPAWN_SUBAGENT 消息，metadata 含 `subagent_id`, `initial_context`, `parent_subagent_id`
6. 返回 `{"subagent_id": "...", "message_id": "..."}`

**与 rt 路由差异**：
- rt：`parent_subagent_id` 来自 `resolve_runtime_ids(runtime_id)`
- agent：`parent_subagent_id` 来自 body

---

#### 3.1.2 `GET /agents/{agent_id}/subagent/{target_subagent_id}/status`

**逻辑**（与 rt_subagent_query 一致，仅 agent_id 来源不同）：
- `agent_id` 来自 URL
- `target_subagent_id` 来自 URL
- 其余逻辑不变：查 subagent、检查 timeout、组装 response（含 runtime_id、result 等）

---

#### 3.1.3 `POST /agents/{agent_id}/subagent/{target_subagent_id}/cancel`

**逻辑**（与 rt_subagent_cancel 一致）：
- `agent_id`、`target_subagent_id` 来自 URL
- 其余逻辑不变

---

#### 3.1.4 `POST /agents/{agent_id}/subagent/report`

**请求体**：
```json
{
  "result": "string",         // 必填
  "subagent_id": "string"     // 必填，调用者（sub-subagent）的 id
}
```

**逻辑**（与 rt_subagent_report 一致，仅 subagent_id 来源不同）：
- rt：`subagent_id` 来自 `resolve_runtime_ids(runtime_id)`
- agent：`subagent_id` 来自 body
- 校验 `subagent_id.startswith("sub-")`
- 调用 `subagent_repo.update_result(subagent_id, agent_id, result)`

---

### 3.2 Gateway - runtime.py 删除 rt SubAgent 路由

**位置**：`novaic-gateway/gateway/api/internal/runtime.py`  
**删除以下 4 个路由**（约 1357–1577 行）：

1. `@router.post("/rt/{runtime_id}/subagent/spawn")` 及 `rt_subagent_spawn`
2. `@router.get("/rt/{runtime_id}/subagent/{target_subagent_id}/status")` 及 `rt_subagent_query`
3. `@router.post("/rt/{runtime_id}/subagent/{target_subagent_id}/cancel")` 及 `rt_subagent_cancel`
4. `@router.post("/rt/{runtime_id}/subagent/report")` 及 `rt_subagent_report`

**删除理由**：
- Tools Server 已使用 agent 路由，无调用方使用 rt 路由
- 统一以 agent 路由为唯一入口

---

### 3.3 RO - 同步改动

**位置**：`novaic-runtime-orchestrator/gateway/api/internal/`

- **agent.py**：新增与 Gateway 相同的 4 个 agent 路由（逻辑一致）
- **runtime.py**：删除与 Gateway 相同的 4 个 rt subagent 路由

**说明**：RO 与 Gateway 共用同一套 internal API 代码结构，需保持同步，以便 RO 独立运行或接收转发时行为一致。

---

### 3.4 Tools Server - executor.py 修改请求体

**位置**：`novaic-tools-server/tools_server/executor.py`

#### 3.4.1 subagent_spawn（约 908–919 行）

**当前**：
```python
response = await client.post(
    f"/internal/agents/{self.agent_id}/subagent/spawn",
    json={
        "task": task_desc,
        "share_context": arguments.get("share_context", False),
        "timeout_minutes": arguments.get("timeout_minutes", 30),
    }
)
```

**修改为**：
```python
response = await client.post(
    f"/internal/agents/{self.agent_id}/subagent/spawn",
    json={
        "task": task_desc,
        "parent_subagent_id": self.subagent_id or "main",  # 新增
        "share_context": arguments.get("share_context", False),
        "timeout_minutes": arguments.get("timeout_minutes", 30),
    }
)
```

**逻辑**：`parent_subagent_id` 表示发起 spawn 的 subagent；main 用 `"main"`，子 agent 用 `self.subagent_id`。

---

#### 3.4.2 subagent_report（约 952–956 行）

**当前**：
```python
response = await client.post(
    f"/internal/agents/{self.agent_id}/subagent/report",
    json={"result": result}
)
```

**修改为**：
```python
response = await client.post(
    f"/internal/agents/{self.agent_id}/subagent/report",
    json={
        "result": result,
        "subagent_id": self.subagent_id,  # 新增
    }
)
```

**逻辑**：report 仅 sub-subagent 可调用，需显式传入 `subagent_id` 供 Gateway 校验。

**前置校验**：executor 已有 `if not self.subagent_id or not self.subagent_id.startswith("sub-")`，可保证 `self.subagent_id` 存在且合法。

---

### 3.5 工具 Schema（可选）

**位置**：`novaic-shared-kernel/src/common/tools/definitions.py` 及各 `common/tools/definitions.py`

- `parent_subagent_id`、`subagent_id` 由 executor 注入，LLM 不传
- Schema 可不改，仅作说明：`parent_subagent_id` 为内部字段，由执行环境填充

---

## 四、转发与部署

### 4.1 转发行为

- `_RO_FORWARDED_PREFIXES` 含 `/internal/rt/`、`/internal/subagents`，不含 `/internal/agents/`
- `/internal/agents/{agent_id}/subagent/*` 在 Gateway 本地处理，不转发到 RO
- SubAgent 创建、状态、取消、上报均走 Gateway 本地 DB（与 memory、notebook 等一致）

### 4.2 部署影响

- Gateway 与 RO 共享同一 DB 时，agent 路由在 Gateway 中操作 SubAgent 表，与 RO 无冲突
- 无新增配置或环境变量

---

## 五、测试要点

1. **subagent_spawn**：main 和 sub-subagent 发起 spawn，均能成功创建子 agent
2. **share_context**：`share_context=true` 时，子 agent 能拿到 parent 的 context
3. **subagent_query / cancel**：能正确查询和取消目标 subagent
4. **subagent_report**：sub-subagent 能成功上报 result，parent 能查到
5. **rt 路由**：删除后，对 `/internal/rt/xxx/subagent/*` 的请求应返回 404（当前无调用方）

---

## 六、改动顺序建议

1. Gateway agent.py：新增 4 个 agent 路由
2. Tools Server executor：修改 spawn、report 的请求体
3. 联调验证 agent 路由
4. Gateway runtime.py：删除 4 个 rt 路由
5. RO：同步 agent.py 与 runtime.py 改动
6. 回归测试

---

## 七、评审检查项

- [ ] spawn 的 `parent_subagent_id` 必填，缺则 400
- [ ] report 的 `subagent_id` 必填，且需 `startswith("sub-")`
- [ ] main 作为 parent 时，`parent_subagent_id` 传 `"main"`
- [ ] share_context 使用 `get_active_runtime(parent_subagent_id, agent_id)` 获取 context
- [ ] 删除 rt 路由前确认无其他调用方
