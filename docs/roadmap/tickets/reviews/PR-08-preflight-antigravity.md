# PR-08: AgentOwnershipResolver 调研报告

## 1. File:Line 表

| 文件 | 修改范围 | 修改说明 |
| --- | --- | --- |
| `novaic-common/common/agents/ownership.py` | 替换现有的 placeholder `AgentOwnershipResolver` | 实现 HTTP 调用的 `resolve` 方法。**【严禁约束】绝对禁止导入 `business.*` 模块**，只能使用 `internal_client` 通过 HTTP 调取 PR-07 的内部接口。 |
| *(未来调用方)* `queue_service/assembler/dispatch.py` | - | PR-10 `DispatchAssembler` 将接入此 Resolver 以获取 owner 身份并做批量与缓存处理。 |
| *(未来调用方)* `novaic-cortex/novaic_cortex/auth.py` | - | Cortex 未来的统一鉴权层可能复用此逻辑获取 user_id 校验凭证。 |
| *(未来调用方)* `novaic-gateway/...` | - | Gateway 的 WebSocket handler 关联检查。 |

## 2. 测试 Checklist

### 单元测试 (`novaic-common/tests/test_ownership.py`)
- [ ] **HTTP 200 命中**：Mock `internal_client` 的 HTTP 返回 200 `{"user_id": "..."}`，验证 `resolve` 返回预期的 `user_id`。
- [ ] **HTTP 404 映射**：Mock HTTP 返回 404，不论是 "agent not found" 还是 "agent has no owner"，均验证函数抛出 `AgentNotOwnedError` 异常。
- [ ] **网络/服务器异常**：Mock HTTP 触发超时或 5xx 错误，验证不伪装成 404，而是抛出 `DispatchError(kind="network")` 或底层网络异常。

### 集成环境验证
- [ ] 确保 PR-07 的 Business 节点运行，手动编写临时脚本或 `curl` 调用，校验真实返回。

## 3. SSOT 声明

- **唯一入口/出口**：所有权鉴别的内部逻辑必须由 `AgentOwnershipResolver.resolve(agent_id)` 承载。
- **异常收敛**：`AgentNotOwnedError` 作为统一向外抛出的未授权/无归属异常，下游服务无需也不应关心底层是 Agent 被删了还是本身无主，达到**屏蔽底层领域细节**的目的。
- **纯粹的网络契约**：调用者只需要提供 `business_base_url` 与 `agent_id`。

## 4. 范围边界

- **纯函数代理**：本 PR 中实现的 `AgentOwnershipResolver` 将只是纯函数/无状态网络调用包装。
- **严守 HTTP 边界**：跨服务的数据只允许通过 PR-07 提供的内部端点（`GET /internal/agents/{agent_id}/owner`）拉取，绝不可在 `novaic-common` 中引入对任何 `entity_store` 的依赖，以维持真正的微服务边界 (R2/R3 底线)。

## 5. 延后项

- **TTL 缓存延后**：原定在 Resolver 类中实现的 5 分钟 TTL 缓存机制，**在此 PR 中不实施**。为了提升批量拉取效率和管理，将缓存统一延后至 PR-10 的 `DispatchAssembler` 层去实施。
- **工厂注入延后**：如何在各服务中注入并持有这个 Resolver 实例（例如是否需要全局 `get_resolver()` 单例工厂），延后到实际接入此组件的 PR-10 等后续任务中处理。
