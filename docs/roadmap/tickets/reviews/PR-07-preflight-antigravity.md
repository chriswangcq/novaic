# PR-07: Business agent-owner endpoint 调研报告

## 1. File:Line 表

| 文件 | 修改范围 | 修改说明 |
| --- | --- | --- |
| `novaic-business/business/internal/agent.py` | ~ 行 43 (新起一段) | 新增 `@router.get("/{agent_id}/owner")` 路由，提供 `agent_id` 到 `user_id` 的权威查询 |

## 2. 测试 Checklist

### 单测 (`novaic-business/tests/test_internal_agents.py` 或等价文件)
- [ ] **正常查询**：构造包含 `user_id` 的 agent 实体，请求 `GET /internal/agents/{agent_id}/owner` 返回 200 及对应 `user_id`。
- [ ] **不存在的 Agent**：请求不存在的 agent_id，返回 404 及 `"error": "agent not found"`。
- [ ] **无 Owner 的 Agent**：构造 `user_id` 为空（或完全没有该字段）的 agent 实体，请求端点返回 404 及 `"error": "agent has no owner"`。

### 集成测试
- [ ] 启动 Business 服务，使用 `curl -H "X-Internal-Key: $NOVAIC_INTERNAL_KEY" -H "X-Internal-Service: test" http://localhost:19998/internal/agents/<agent_id>/owner` 验证返回结构是否符合预期。

## 3. SSOT 声明

- **权威数据源**：`agent_id` 对应的 `owner user_id` 将唯一由 Business 服务的 `GET /internal/agents/{agent_id}/owner` 端点提供。后续的 `AgentOwnershipResolver` (PR-08) 和 `DispatchAssembler` (PR-10) 均强制依赖此端点，不直接查询底层数据库。
- **字段兜底规范**：若数据库层存在命名不一致（如 `owner_user_id` 与 `user_id`），由该端点负责向上统一屏蔽差异，对外一律输出规范的 `"user_id"`。

## 4. 范围边界

- **仅处理只读查询**：本 PR 仅实现 `GET /internal/agents/{agent_id}/owner` 端点，不负责修改、创建 agent 或维护所有权变更的逻辑。
- **强依赖缺失则 404**：对于 "存在 agent 但 user_id IS NULL" 的情况，服务端明确返回 404 语义，以便下游直接按 "未归属 / 找不到" 处理（触发 `AgentNotOwnedError`）。
- **非 DB 修改**：不在此 PR 中调整 Entangled 的 `agents` Schema。

## 5. 延后项

- **性能优化**：由于每次查询均调用该端点，在高并发场景下可能有性能损耗，可延后至 PR-08 讨论是否需要在 Gateway/Resolver 层增加 TTL 缓存。
- **内部调用的 metrics 记录**：`internal_requests_total` 指标的记录与规范统一已推迟到 PR-19 后的集中 cleanup 阶段。
