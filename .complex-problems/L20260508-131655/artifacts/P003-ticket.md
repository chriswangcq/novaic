# P003 Ticket - 审计显式依赖边界与 side-effect adapter

## Problem Definition

审计当前 FSM/worker/session/cortex 相关代码是否还存在隐藏输入或 side effect 泄漏：直接读取 env/time/uuid/global config、直接创建 HTTP client、业务层直接执行外部 IO 等。

## Proposed Solution

只读检查：

- `queue_service/dependencies.py`
- `task_queue/workers/dependencies.py`
- `queue_service/session_repo.py`
- `queue_service/queue_db.py`
- `queue_service/saga_repo.py`
- `task_queue/workers/*_effects.py`
- `task_queue/workers/*_execution.py` / action engines
- `novaic-cortex/novaic_cortex/blob_payload.py`
- `novaic-cortex/novaic_cortex/blob_store.py`

搜索 `os.environ/os.getenv/datetime.now/utc_now_iso/uuid.uuid4/time.time/httpx.Client/httpx.AsyncClient` 等隐藏输入。

## Acceptance Criteria

- 列出显式边界已达成项。
- 列出仍可接受的边界 factory 与不可接受的业务隐藏输入。
- 判断 side effect adapter 是否集中。
- 运行依赖边界和 effect plan 相关测试/脚本。

## Verification Plan

- `rg` 搜索隐藏输入。
- 读取 dependency provider 和 effect adapters。
- 运行 action engine/effect boundary tests。
- 运行或引用 HTTP client lint/guard。

## Risks

- 某些 `from_env()` 或 `.system()` 是边界 factory，不应误判为业务隐式输入。
- 某些时间解析不是时间生成，需要区分。

## Assumptions

- 本票只审计，不改代码。
