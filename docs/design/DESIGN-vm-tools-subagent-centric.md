# 设计方案：VM Tools API 改为 Subagent 维度

## 一、目标

将 VM 工具发现 API 从 `runtime_id` 改为 `agent_id` + `subagent_id`，使 Gateway 可本地处理，摆脱对 RO 的转发依赖。

---

## 二、当前逻辑分析

```
runtime_id → RuntimeRepository.get_by_id → agent_id
agent_id   → get_agent_config_manager   → 检查 agent.vm
→ 返回 VM_TOOLS（若 agent 有 vm 配置）
```

**runtime_id 的唯一作用**：解析出 agent_id。VM 可用性完全由 agent 配置决定，与 runtime 无关。

**Gateway 问题**：B2 下 agent_runtimes 已清空，fallback 恒 404。

---

## 三、新 API 规范

### 3.1 路径

```
GET /internal/subagents/{agent_id}/{subagent_id}/vm-tools
```

### 3.2 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| agent_id | string | 是 | Agent ID |
| subagent_id | string | 是 | SubAgent ID（main、sub-xxx 等） |

### 3.3 响应格式

**成功（有 VM 配置）**：200

```json
{
  "tools": [
    {
      "name": "screenshot",
      "description": "...",
      "inputSchema": { ... }
    }
  ],
  "agent_id": "agent-xxx",
  "subagent_id": "main",
  "vm_available": true
}
```

**成功（无 VM 配置）**：200

```json
{
  "tools": [],
  "agent_id": "agent-xxx",
  "subagent_id": "main",
  "vm_available": false
}
```

**失败**：404

```json
{
  "detail": "SubAgent not found"
}
```

### 3.4 错误码

| 状态码 | 场景 |
|--------|------|
| 404 | SubAgent 不存在 |
| 200 | 其他情况（agent 不存在、无 vm 配置等）均返回 200，vm_available=false |

---

## 四、实现逻辑（Gateway 本地）

### 4.1 处理流程

```
1. SubAgentRepository.get_by_id(subagent_id, agent_id)
   → 不存在则 404

2. get_agent_config_manager().get_agent(agent_id)
   → 异常或 agent 不存在 → 返回 {tools:[], vm_available:false, error?:...}

3. 检查 agent.vm
   → 无 vm 或 vm 为空 → 返回 {tools:[], agent_id, subagent_id, vm_available:false}

4. 返回 {tools: VM_TOOLS, agent_id, subagent_id, vm_available:true}
```

### 4.2 依赖

| 依赖 | 来源 | 说明 |
|------|------|------|
| SubAgentRepository | gateway.db.repositories | 校验 subagent 存在 |
| get_agent_config_manager | gateway.config.agents | 读 agents 表 |
| VM_TOOLS | common.tools | 工具定义 |

**不依赖**：RuntimeRepository、agent_runtimes、maybe_forward、RO

### 4.3 实现位置

**Gateway**：`novaic-gateway/gateway/api/internal/vm.py`

- 新增 `GET /subagents/{agent_id}/{subagent_id}/vm-tools`
- 路由挂载在 vm_router 下，完整路径 `/internal/subagents/{agent_id}/{subagent_id}/vm-tools`

### 4.4 伪代码

```python
@router.get("/subagents/{agent_id}/{subagent_id}/vm-tools")
async def get_subagent_vm_tools(agent_id: str, subagent_id: str):
    db = get_db()
    subagent_repo = SubAgentRepository(db)
    if not subagent_repo.get_by_id(subagent_id, agent_id):
        raise HTTPException(404, "SubAgent not found")

    config_mgr = get_agent_config_manager()
    try:
        agent = config_mgr.get_agent(agent_id)
    except Exception as e:
        return {"tools": [], "agent_id": agent_id, "subagent_id": subagent_id,
                "vm_available": False, "error": str(e)}

    if not getattr(agent, "vm", None) or not agent.vm:
        return {"tools": [], "agent_id": agent_id, "subagent_id": subagent_id,
                "vm_available": False}

    return {
        "tools": VM_TOOLS,
        "agent_id": agent_id,
        "subagent_id": subagent_id,
        "vm_available": True,
    }
```

---

## 五、旧 API 处理

### 5.1 `GET /internal/runtimes/{runtime_id}/vm-tools`

| 服务 | 处理 |
|------|------|
| **Gateway** | 删除该端点（或标记 deprecated，返回 410 Gone） |
| **RO** | 保留，供 RO 内部/兼容调用 |

### 5.2 调用方迁移

当前无生产调用方。若未来有：

- 原：`GET {GATEWAY}/internal/runtimes/{runtime_id}/vm-tools`
- 新：`GET {GATEWAY}/internal/subagents/{agent_id}/{subagent_id}/vm-tools`

调用方需在上下文中持有 `agent_id`、`subagent_id`（与 tool-context、tools 等 subagent API 一致）。

---

## 六、RO 侧

- **不新增** subagent 版本：vm-tools 由 Gateway 独占，RO 不再提供
- **保留** `GET /internal/runtimes/{runtime_id}/vm-tools`：仅 RO 内部使用（若有）

---

## 七、与现有 API 对齐

| API | 路径模式 | 说明 |
|-----|----------|------|
| tool-context | `/internal/subagents/{agent_id}/{subagent_id}/tool-context` | 同模式 |
| tool-ports | `/internal/subagents/{agent_id}/{subagent_id}/tool-ports` | 同模式 |
| **vm-tools（新）** | `/internal/subagents/{agent_id}/{subagent_id}/vm-tools` | 新增 |

---

## 八、验收标准

1. Gateway 提供 `GET /internal/subagents/{agent_id}/{subagent_id}/vm-tools`
2. 校验 subagent 存在，不存在返回 404
3. 不依赖 RuntimeRepository、agent_runtimes、maybe_forward
4. 响应含 `tools`、`agent_id`、`subagent_id`、`vm_available`
5. Gateway 删除或废弃 `GET /internal/runtimes/{runtime_id}/vm-tools`
