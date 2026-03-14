# 调研报告：Gateway Runtime 相关逻辑使用情况

## 一、调研范围

1. Gateway 需要转发的 API 是否有人调用？
2. message.py INTERRUPT、subagent.py /status 的合规性
3. RuntimeRepository、agent_runtimes、resolve_runtime_ids、get_runtime_context 是否还有用

---

## 二、Gateway 转发 API 是否有人调用？

### 2.1 maybe_forward 的路径匹配

**文件**：`novaic-gateway/gateway/api/internal/helpers.py` L160-163

```python
_RO_FORWARDED_PREFIXES = [
    "/internal/runtimes",
    "/internal/rt/",
]
```

**只有**以 `/internal/runtimes` 或 `/internal/rt/` 开头的路径才会被转发到 RO。

### 2.2 Gateway 是否暴露这些路径？

**文件**：`novaic-gateway/gateway/api/internal_proxy.py`

- Phase 4 已移除 runtime_router
- Gateway 的 internal 路由**不包含** `/internal/runtimes/*`、`/internal/rt/*`
- 对比：`novaic-runtime-orchestrator` 的 internal 包含 runtime_router，RO 自己暴露这些路径

### 2.3 subagent/message 路径会转发吗？

| 端点 | 传给 maybe_forward 的 path | 是否匹配 _RO_FORWARDED_PREFIXES |
|------|---------------------------|--------------------------------|
| subagent due-wake, status, cancel 等 | `/internal/subagents/*` | ❌ 不匹配 |
| message interrupt, unread, claim 等 | `/internal/messages/*`、`/internal/agents/*` | ❌ 不匹配 |

**结论**：`maybe_forward_to_runtime_orchestrator` 对 subagent、message 路径**永远返回 None**，全部走本地逻辑。

### 2.4 谁调用 /internal/runtimes/*、/internal/rt/*？

| 调用方 | 目标 | 说明 |
|--------|------|------|
| **Tools Server** GatewayInternalClient | gateway_url | 已改为 subagent API，不再调 /internal/runtimes/* |
| **agent-runtime** UnifiedInternalClient | internal_url (RO) | `/internal/runtimes/*` 走 RO，不经过 Gateway |
| **RO** 自身 | - | 自己处理，不经过 Gateway |

### 2.5 结论

**Gateway 的 maybe_forward 转发逻辑实际上从未生效**：

1. Gateway 不暴露 `/internal/runtimes/*`、`/internal/rt/*`，没有请求会命中这些路由
2. subagent、message 路径不匹配转发前缀，always 走本地
3. 调用方要么直连 RO，要么已改用 subagent API

---

## 三、message.py INTERRUPT 与 subagent.py /status 合规性

### 3.1 message.py INTERRUPT

**文件**：`novaic-gateway/gateway/api/internal/message.py` L86-138

```python
@router.post("/agents/{agent_id}/interrupt")
async def interrupt_agent(agent_id: str):
    # maybe_forward("/internal/agents/{agent_id}/interrupt") → None（不匹配）
    with db.transaction(...):
        runtime_cursor = db.execute("""
            UPDATE agent_runtimes
            SET status = 'completed', phase = 'completed', updated_at = ?
            WHERE agent_id = ? AND status = 'active'
        """, ...)
        interrupted_runtimes = runtime_cursor.rowcount
        ...
```

**v40 迁移**：`DELETE FROM agent_runtimes`（Gateway 不再拥有 runtime）

**结果**：`agent_runtimes` 恒为空，`UPDATE` 影响 0 行，`interrupted_runtimes` 恒为 0。**不合规**：Gateway 不应再写已清空的表。

### 3.2 subagent.py /status

**文件**：`novaic-gateway/gateway/api/internal/subagent.py` L636-712

```python
@router.get("/subagents/{agent_id}/{subagent_id}/status")
async def get_subagent_status(...):
    # maybe_forward → None
    ...
    runtimes = runtime_repo.get_latest_runtimes(subagent_id, agent_id, limit=1)
    if runtimes:
        response["runtime_id"] = runtime.runtime_id
        response["runtime_status"] = runtime.status
        ...
```

**RuntimeRepository.get_latest_runtimes**：查询 `agent_runtimes` 表

**结果**：v40 后表为空，`get_latest_runtimes` 恒返回 `[]`，`runtime_id`、`runtime_status` 永远不设置。**不合规**：Gateway 不应再依赖已清空的 agent_runtimes 做业务逻辑。

---

## 四、RuntimeRepository、agent_runtimes、resolve_runtime_ids、get_runtime_context 是否还有用？

### 4.1 调用关系

| 符号 | Gateway 内调用者 |
|------|------------------|
| **resolve_runtime_ids** | subagent.py, message.py, agent.py, self_drive.py, task.py, config.py, llm.py, health.py, broadcast.py, web.py |
| **get_runtime_context** | config.py (L283), llm.py, agent.py, message.py, health.py, broadcast.py, web.py |
| **RuntimeRepository** | helpers.py（上述两函数）、subagent.py（get_latest_runtimes） |
| **agent_runtimes 表** | RuntimeRepository 全部 CRUD、message.py INTERRUPT UPDATE |

### 4.2 数据来源

| 组件 | 数据库 | agent_runtimes 状态 |
|------|--------|---------------------|
| **Gateway** | gateway.db | v40 已清空 |
| **RO** | runtime_orchestrator.db | 有数据，RO 拥有 runtime |

### 4.3 Gateway  standalone 行为

- `resolve_runtime_ids(runtime_id)` → `RuntimeRepository.get_by_id` → 查 gateway.db.agent_runtimes → 空 → **404**
- `get_runtime_context(runtime_id)` → 同上 → **404**
- 所有依赖这两个函数的 internal API（config/llm/runtime、task、llm、health 等）在 Gateway  standalone 下都会 404

### 4.4 谁调用这些 Gateway API？

**agent-runtime** 的 `UnifiedInternalClient._is_gateway_internal_path` 将 `/internal/config/` 判为 Gateway 路径，因此：

- `GET /internal/config/llm/runtime/{runtime_id}` → 发往 **gateway_url**（Gateway）
- Gateway 的 config 使用 `get_runtime_context` → agent_runtimes 空 → **404**

即：在 Gateway 与 RO 分离部署时，依赖 runtime 的 config/llm 等接口在 Gateway 侧会失败。

### 4.5 RO 侧（novaic-runtime-orchestrator）

- RO 有 runtime_router，使用 `runtime_orchestrator.db`，agent_runtimes 有数据
- RO 的 `resolve_runtime_ids`、`get_runtime_context`、`RuntimeRepository` 正常工作
- agent-runtime 的 runtime 相关请求（如 get_runtime）发往 internal_url (RO)，可正常返回

### 4.6 结论

| 组件 | resolve_runtime_ids / get_runtime_context / RuntimeRepository | 状态 |
|------|---------------------------------------------------------------|------|
| **Gateway** | 查 gateway.db.agent_runtimes（空） | **无效**，相关接口会 404 |
| **RO** | 查 runtime_orchestrator.db.agent_runtimes（有数据） | **有效** |

Gateway 侧的 RuntimeRepository、agent_runtimes、resolve_runtime_ids、get_runtime_context 在 v40 后已无实际作用，属于死逻辑。

---

## 五、修复建议

| # | 项目 | 建议 |
|---|------|------|
| 1 | maybe_forward_to_runtime_orchestrator | 移除或大幅简化：当前转发路径从未命中 |
| 2 | message.py INTERRUPT 的 UPDATE agent_runtimes | 删除该 UPDATE，或改为转发到 RO 的 interrupt |
| 3 | subagent.py /status 的 get_latest_runtimes | 删除该分支，或改为转发到 RO 的 status |
| 4 | Gateway resolve_runtime_ids、get_runtime_context、RuntimeRepository | 移除或改为转发到 RO；依赖 runtime 的 config/llm 等接口应改为调用 RO |
| 5 | agent-runtime 路由 | `/internal/config/llm/runtime/*` 应发往 RO 而非 Gateway（因 runtime 数据在 RO） |

---

## 六、相关文档

- [IMPLEMENTATION-PLAN-runtime-cleanup-subagent-centric.md](./IMPLEMENTATION-PLAN-runtime-cleanup-subagent-centric.md)
- [REVIEW-REPORT-tools-server-runtime-cleanup.md](./REVIEW-REPORT-tools-server-runtime-cleanup.md)
