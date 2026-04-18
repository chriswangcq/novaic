# PR-08: AgentOwnershipResolver 调研报告

## 1. File:Line 表

| 文件 | 修改范围 | 修改说明 | 本 PR 动作 |
| --- | --- | --- | --- |
| `novaic-common/common/agents/ownership.py` | 替换现有的 placeholder `AgentOwnershipResolver` | 实现 HTTP 调用、TTL 缓存、并发锁、以及全局 `get_resolver()`。**【严禁约束】绝对禁止导入 `business.*` 模块**。 | 实现核心逻辑 |
| `novaic-common/common/wake/errors.py` | `DispatchError` 定义 | 最小扩展 `DispatchError.__init__(msg="", *, kind=None, status=None)` 以支持 `kind="network"` 初始化避免 TypeError。 | 补齐异常签名 |
| *(未来调用方)* `queue_service/assembler/dispatch.py` | - | PR-10 `DispatchAssembler` 将接入此 Resolver 以获取 owner 身份并做批量与缓存处理。 | 不改动，仅登记 SSOT 约束 |
| *(未来调用方)* `novaic-cortex/novaic_cortex/auth.py` | - | Cortex 未来的统一鉴权层可能复用此逻辑获取 user_id 校验凭证。 | 不改动，仅登记 SSOT 约束 |
| *(未来调用方)* `novaic-gateway/...` | - | Gateway 的 WebSocket handler 关联检查。 | 不改动，仅登记 SSOT 约束 |

## 2. 测试 Checklist

*(遵循静态调研规范，实施状态将仅在 Ticket 正文中维护)*

### 单元测试 (`novaic-common/tests/test_ownership.py`)
> 测试基于 `pytest-httpx` 打真实路径 `/internal/agents/{id}/owner`。
- [ ] **命中**：第一次拉取后命中缓存，直接返回（断言 0 次新 HTTP 调用）。
- [ ] **首次获取**：发起 1 次 HTTP 拿到 200，结果进入缓存。
- [ ] **TTL 过期**：通过 monkeypatch `_now()` 模拟过期，断言再发 1 次 HTTP 请求。
- [ ] **404 映射**：Mock HTTP 返回 404，不论是 "not found" 还是 "no owner"，均断言抛出 `AgentNotOwnedError` 异常。
- [ ] **网络错误**：Mock HTTP 触发网络错误，断言抛出 `DispatchError(kind="network")`，不伪装成 404。
- [ ] **并发防击穿**：使用 `asyncio.gather` 并发 resolve 同一 `agent_id`，断言底层的 HTTP 调用确实只发生 1 次。

### 集成环境验证
- [ ] 确保 PR-07 的 Business 节点运行，执行 Python 性能测试脚本验证耗时 <1ms 且无 ImportError。

## 3. SSOT 声明

- **异常勘误**：Ticket 示例代码中的 `internal_client` 是笔误，实际应使用异步版本的 `internal_async_client`。
- **不缓存负例**：遇到 404 绝不将负面结果存入 TTL 缓存，以避免 "新建 agent 但缓存认为 no owner" 的竞态错误。
- **唯一入口/出口**：所有权鉴别的内部逻辑必须由 `AgentOwnershipResolver.resolve(agent_id)` 承载，只抛 `AgentNotOwnedError` 或网络异常。
- **纯粹的网络契约**：调用者只需从环境变量 `BUSINESS_INTERNAL_URL` 注入工厂函数。

## 4. 范围边界

- **纯网络代理与缓存**：本 PR 中实现的 `AgentOwnershipResolver` 是带 TTL 与锁的微服务端点封装。
- **严守 HTTP 边界**：跨服务的数据只允许通过 PR-07 提供的内部端点（`GET /internal/agents/{agent_id}/owner`）拉取，绝不可在 `novaic-common` 中引入对任何 `entity_store` 的依赖，以维持真正的微服务边界 (R2/R3 底线)。

## 5. 延后项

- （无具体业务逻辑延后项，按 Ticket 全量实现缓存与工厂注入）
