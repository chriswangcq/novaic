# SubAgent DB/Log 分析报告

## 1. DB 现状对比

### gateway.db subagents
| subagent_id | agent_id | status | created_at |
|-------------|-----------|--------|------------|
| sub-e40ce1c6cada | fe9868c8-... | sleeping | 2026-03-01T11:15:32 |

### runtime_orchestrator.db subagents
| subagent_id | agent_id | status | created_at |
|-------------|-----------|--------|------------|
| sub-328408169365 | fe9868c8-... | sleeping | 2026-03-01T11:35:52 |
| sub-60a9bd0b018d | fe9868c8-... | sleeping | 2026-03-01T11:35:39 |
| main-fe9868c8 | fe9868c8-... | sleeping | 2026-02-24 |

**结论**：`sub-e40ce1c6cada` 仅存在于 gateway.db，不在 runtime_orchestrator.db。

---

## 2. 根因链

### 2.1 调用链
1. **Tools Server** 调用 `POST /internal/agents/{agent_id}/subagent/spawn` → 发往 Gateway
2. **Task Worker (message_route)** 调用：
   - `GET /internal/subagents/{agent_id}/{subagent_id}/status` → 发往 RO
   - `POST /internal/runtimes/get-or-create` → 发往 RO

### 2.2 sub-e40ce1c6cada 失败时间线 (11:15 UTC+8)

| 时间 | 事件 | 结果 |
|------|------|------|
| 11:15:32 | subagent_spawn 在 Gateway 本地处理 | 写入 **gateway.db** |
| 11:15:32 | message_route: get_subagent_status → RO | **404** SubAgent not found（RO 的 subagents 表无此记录） |
| 11:15:32 | message_route: get_or_create_runtime → RO | **500** Internal Server Error |

### 2.3 500 的具体原因

`agent_runtimes` 表有外键：
```sql
FOREIGN KEY (subagent_id) REFERENCES subagents(subagent_id) ON DELETE CASCADE
```

`get_or_create_active_runtime` 会向 `agent_runtimes` 插入新 runtime。若 `subagent_id` 在 RO 的 `subagents` 表中不存在，INSERT 会触发外键约束失败 → 未捕获异常 → 500。

---

## 3. 11:35 成功案例

Gateway 日志显示 11:35 的 spawn 已转发到 RO：
```
httpx: POST http://127.0.0.1:19993/internal/agents/.../subagent/spawn "HTTP/1.1 200 OK"
```

对应 subagent `sub-60a9bd0b018d`、`sub-328408169365` 已出现在 runtime_orchestrator.db，说明转发逻辑在 11:35 已生效。

---

## 4. 结论与建议

### 根因
- **11:15**：subagent_spawn 仍在 Gateway 本地处理，只写入 gateway.db
- RO 的 get-or-create 依赖 subagents 表，subagent 缺失导致外键失败 → 500

### 已实施的修复
- 精确路径转发：5 个 agent subagent 接口转发到 RO
- subagent_spawn 现由 RO 处理，subagent 写入 runtime_orchestrator.db

### 建议
1. **新 spawn**：使用新 build 后，subagent 会正确写入 RO，问题应已解决
2. **历史脏数据**：gateway.db 中的 `sub-e40ce1c6cada` 为孤立记录，可考虑：
   - 若该 subagent 已无业务意义：可忽略或手动清理
   - 若需保留：需在 runtime_orchestrator.db 中补插对应 subagent（不推荐，易出错）

### 验证方式
1. 重启 App，使用新 build
2. 触发新的 subagent_spawn
3. 检查 runtime_orchestrator.db：`SELECT * FROM subagents ORDER BY created_at DESC LIMIT 5;`
4. 确认 task-worker 日志无 "Runtime not found" 或 "Internal Server Error"
