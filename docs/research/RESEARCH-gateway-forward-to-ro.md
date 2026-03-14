# 研究报告：Gateway 是否还需 Forward 到 RO

## 一、结论

**Gateway 不再需要 forward 到 RO。** `maybe_forward_to_runtime_orchestrator` 当前为**死代码**，可安全移除。

---

## 二、转发配置

```python
# helpers.py
_RO_FORWARDED_PREFIXES = [
    "/internal/runtimes",
    "/internal/rt/",
]
```

**只有**以 `/internal/runtimes` 或 `/internal/rt/` 开头的路径才会被转发。

---

## 三、maybe_forward 调用路径分析

### 3.1 subagent.py（约 20 处）

| 路径 | 是否匹配 _RO_FORWARDED_PREFIXES |
|------|--------------------------------|
| `/internal/subagents/due-wake` | ❌ |
| `/internal/subagents/{agent_id}/main` | ❌ |
| `/internal/subagents/{agent_id}/{subagent_id}` | ❌ |
| `/internal/subagents/{agent_id}/{subagent_id}/status` | ❌ |
| `/internal/subagents/{agent_id}/{subagent_id}/cancel` | ❌ |
| `/internal/agents/{agent_id}/drive` | ❌ |
| `/internal/agents/{agent_id}/notebook-summary` | ❌ |
| ... | ❌ |

### 3.2 message.py（约 15 处）

| 路径 | 是否匹配 |
|------|----------|
| `/internal/messages/unread/{agent_id}` | ❌ |
| `/internal/messages/claim-and-prepare` | ❌ |
| `/internal/messages/{id}/confirm` | ❌ |
| ... | ❌ |

### 3.3 vm.py

- **已删除**：`GET /internal/runtimes/{runtime_id}/vm-tools`（唯一会匹配的端点）
- **现仅有**：`GET /internal/subagents/{agent_id}/{subagent_id}/vm-tools`（不匹配）

---

## 四、Gateway 当前 Internal 路由

| 模块 | 路径模式 | 是否匹配转发前缀 |
|------|----------|------------------|
| vm | `/vm/*`, `/subagents/*/vm-tools` | ❌ |
| subagent | `/subagents/*` | ❌ |
| message | `/messages/*`, `/chat/*`, `/agents/*/chat/*` | ❌ |
| agent | `/agents/*` | ❌ |
| task | `/tasks/*`, `/rt/*`, `/agents/*/quadrant-tasks` | `/rt/*` 匹配 |
| self_drive | `/rt/*/self-drive/*` | `/rt/*` 匹配 |
| config, health, ... | 其他 | ❌ |

### 4.1 `/internal/rt/*` 路由的实际处理

- `task.py`、`self_drive.py` 中的 `/rt/{runtime_id}/*` 使用 `resolve_runtime_ids(runtime_id)` 本地解析
- **不调用** `maybe_forward`，直接本地处理
- 但 Gateway 的 `agent_runtimes` 已清空（v40），`resolve_runtime_ids` 会 404

### 4.2 谁在调用 `/internal/rt/*`？

- **Tools Server** `GatewayInternalClient`：`path.startswith("/internal/")` 时使用 `internal_url` = **RO**
- **RO** `task_queue/client`：调用 RO 自身
- 因此 `/internal/rt/*` 请求实际发往 **RO**，不经过 Gateway

---

## 五、调用方与入口

| 调用方 | 目标 | 说明 |
|--------|------|------|
| Tools Server api / runtime_manager | GATEWAY_URL | subagent tool-context、tool-ports、with-tools |
| Tools Server GatewayInternalClient | RO (internal_url) | runtimes、rt、quadrant-tasks、self-drive |
| RO | GATEWAY_URL | subagent/main、context/append 等 |
| agent-runtime | GATEWAY_URL | config、tools 等 |

**结论**：Gateway 收到的 internal 请求均为 `/internal/subagents/*`、`/internal/agents/*`、`/internal/messages/*`、`/internal/config/*` 等，**无一**落在 `_RO_FORWARDED_PREFIXES` 中。

---

## 六、client.forward 出站调用（非转发）

`agent.py`、`subagent.py` 中的 `client.forward()` 是 Gateway **主动调用 RO**，例如：

- `GET /internal/runtimes/latest/{agent_id}/{subagent_id}`
- `POST /internal/runtimes/cancel-by-subagent`
- `POST /internal/runtimes/delete-by-subagent`

这是出站 HTTP 调用，不是入站请求的转发，应保留。

---

## 七、建议

### 7.1 可安全执行

1. **清空** `_RO_FORWARDED_PREFIXES`，或
2. **删除** `maybe_forward_to_runtime_orchestrator` 及所有调用

### 7.2 清理步骤

1. 在 `helpers.py` 中删除 `maybe_forward_to_runtime_orchestrator` 及 `_RO_FORWARDED_PREFIXES`
2. 在 `subagent.py`、`message.py` 中删除所有 `proxied = await maybe_forward_...` 及 `if proxied is not None: return proxied` 分支
3. 保留 `client.forward` 出站调用

### 7.3 影响

- 无功能影响：当前没有任何请求会走转发逻辑
- 代码更简单，无死代码
