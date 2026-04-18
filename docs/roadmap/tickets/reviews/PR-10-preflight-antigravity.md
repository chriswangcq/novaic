# PR-10: DispatchAssembler 调研与落地计划 (Preflight Review)

## 1. 目标与定位

实现 `DispatchAssembler`，作为未来所有唤醒触发动作（User Message, Timer, Event 等）向 Queue Service 投递的 **唯一单点（Single Entry Point）**。
在此之前，`AgentOwnershipResolver`（所有权）和 `TriggerType`（强类型枚举）均已在 PR-08 / PR-09 落地，PR-10 负责将它们组装成一个内聚的组件。

## 2. File:Line 落地与变更策略

| 文件路径 | 修改动作与目标 |
| --- | --- |
| `novaic-common/common/wake/assembler.py` | **核心逻辑实现**：定义 `DispatchRequest`, `DispatchResult` dataclass，以及 `DispatchAssembler` 类。`assemble()` 负责通过 resolver 获取 user_id 并拼接参数；`dispatch()` 负责调用 internal_client 将组装好的 payload 发送给 Queue Service `/dispatch` 接口。 |
| `novaic-common/common/wake/errors.py` | **扩展异常**：在现有的 `DispatchError` 中，新增对 `kind` 的支持 (`"bad_argument"`, `"no_owner"`, `"queue_400"`, `"queue_5xx"`, `"network"`)，并在抛出时将 HTTPException 等转换为此内置异常。 |
| `novaic-common/common/wake/__init__.py` | **暴露出口**：在 `__all__` 中暴露 `DispatchAssembler`, `DispatchRequest`, `DispatchResult`。 |
| `novaic-common/tests/test_assembler.py` | **单测**：覆盖各种异常路径（无 owner、400、500、网络断开等）与正常组装路径。 |
| `novaic-common/tests/contract/test_assembler_queue_schema.py` | **合约测试**：调用 `to_queue_payload()`，并强行将其喂给 `novaic-agent-runtime.queue_service.routes.DispatchRequest.model_validate`，确保两端 Schema 完全契合。 |

## 3. 测试与验证 Checklist

### 单测 (`test_assembler.py`)
- [ ] `assemble` 成功：验证返回 `DispatchRequest` 且包含 `user_id` 和默认补齐的 `subagent_id`。
- [ ] `assemble` 失败 (非法类型)：传入非 `TriggerType` 引发 `DispatchError(kind="bad_argument")`。
- [ ] `assemble` 失败 (无 Owner)：mock resolver 抛出 `AgentNotOwnedError` -> 转换抛出 `DispatchError(kind="no_owner")`。
- [ ] `dispatch` 成功：mock HTTP 200 返回 -> 返回 `DispatchResult` 对象，提取 `session_id` 和 `buffered` 标志。
- [ ] `dispatch` 异常 (HTTP 4xx/5xx)：返回状态码 \>= 400 抛出 `queue_400`，\>= 500 抛出 `queue_5xx`。
- [ ] `dispatch` 异常 (网络超时)：抓取 `httpx.RequestError` 抛出 `network`。

### 合约测试 (`test_assembler_queue_schema.py`)
- [ ] 跨层级 Schema 对齐验证：生成的 `to_queue_payload()` 必须 100% 满足 Queue Service 端 Pydantic `DispatchRequest` 的所有必填校验和严格校验。

## 4. 可观测性 (Metrics & Logs) 的特殊处理

> **TD 记录/延后项**：
> 鉴于目前 `novaic-common` 中并未引入 `prometheus_client`，全仓范围尚未统一 metric 的采集。若直接在 `assembler.py` 中写 `from prometheus_client import Counter` 会引发导入错误。
>
> **处理策略**：
> - `[-] 暂缓`：将 PR-10 ticket 中的 `dispatch_total` counter 和 `dispatch_latency_seconds` histogram 暂缓，延后到后续指标采集重构（如 PR-19 的单独 cleanup）统一治理。
> - `[ ] 落实`：但 **结构化日志** 必须到位。在 `dispatch` 方法最后以及异常抛出前，使用结构化 log 记录：`event=dispatch trigger=... agent=... user=... messages=... result=ok|<kind>`。

## 5. 范围边界

- **不动调用方**：本次 PR **不修改** Business (PR-11)、HealthWorker (PR-12) 或 SchedulerWorker (PR-13) 的现有调用逻辑。仅提供 `DispatchAssembler` 类供未来 PR 接入。
- **职责纯粹性**：`Assembler` 不包含 retry 和 backoff 逻辑。失败就是 raise，由调用方（或未来的 Subscriber）决定重试。

## 6. 与 PR-08 设计变更的适配

PR-08 验收中明确：`AgentOwnershipResolver.get_resolver()` 被退回为了 sync 方法（避免绑定 event loop）。因此在 `Assembler` 中，我们将通过直接实例化或传入 resolver 实例的方式保证跨 Worker 并发安全，避免单例锁嵌套的坑。
