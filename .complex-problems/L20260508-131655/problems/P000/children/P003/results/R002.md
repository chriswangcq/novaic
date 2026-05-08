# P003 Result - 审计显式依赖边界与 side-effect adapter

## Scope

审计 Queue FSM/worker/Cortex 相关代码的隐藏输入与 side-effect adapter 边界。

## Searches

搜索：

```bash
rg -n "os\\.environ|os\\.getenv|datetime\\.now\\(|utc_now_iso\\(|uuid\\.uuid4\\(|time\\.time\\(|httpx\\.(Async)?Client\\(" \
  novaic-agent-runtime/queue_service \
  novaic-agent-runtime/task_queue \
  novaic-cortex/novaic_cortex -g '*.py'
```

命中分类：

- Queue boundary factories
  - `queue_service/dependencies.py`: `QueueServiceDependencies.system()` 绑定 `utc_now_iso` 和 UUID providers。
  - `task_queue/workers/dependencies.py`: `WorkerRuntimeDependencies.system()` 绑定 `clock_iso`、`monotonic`、`sleeper`、worker/execution token providers。
- Runtime handler boundary
  - `task_queue/utils/activity_projection.py`: `with_system_activity_dependencies(ctx)` 在 handler boundary 绑定 activity clock/order。
- Cortex boundary-ish factories
  - `novaic_cortex/blob_payload.py`: `BlobPayloadPolicy.from_env()` 读取 `CORTEX_PAYLOAD_BLOB_THRESHOLD_BYTES`；`HttpBlobPayloadClient.from_env()` 读取 `CORTEX_BLOB_SERVICE_URL`。
  - `novaic_cortex/registry.py`: `WorkspaceRegistry.__init__()` 默认调用 `BlobPayloadPolicy.from_env()`，且 `clock` 默认 `time.time`。
- Cortex infrastructure internals
  - `novaic_cortex/scope_locks.py`: Redis lock token 使用 `uuid.uuid4().hex`，属于 lock adapter 内部随机 token，不是 Queue FSM decision 输入。
  - `novaic_cortex/auth.py`: token exp 使用 `time.time()`，属于 auth adapter，不在 Queue FSM path。

## Evidence Read

- `queue_service/dependencies.py`
  - Queue domain objects 的 clock/id provider 都由 `QueueServiceDependencies.system()` 注入到 constructors。
- `task_queue/workers/dependencies.py`
  - Worker runtime 的 clock/sleep/worker id/execution token 显式打包。
- `session_repo.py` / `queue_db.py` / `saga_repo.py`
  - 构造器显式接收 clock/id providers。
- `task_queue/workers/*_effects.py`
  - Task/Saga/Health/Scheduler concrete IO 都集中在 effect adapters。
  - Action engines 调用 `execute_effect(...)`，不直接创建 client 或发 HTTP。
- `novaic_cortex/blob_payload.py` / `blob_store.py`
  - 已使用 `common.http.clients.internal_async_client`，没有直接 `httpx.AsyncClient(...)`。
- `novaic_cortex/registry.py`
  - 仍在构造器内读取 env-derived policy/default clock，这是本次审计发现的显式边界 gap。

## Verification

执行：

```bash
rg -n "httpx\\.(Client|AsyncClient)\\(" novaic-agent-runtime novaic-cortex -g '*.py' || true
bash scripts/ci/lint_httpx.sh
python3 scripts/ci/check_no_internal_async.py
```

结果：

- direct `httpx.Client(...)` / `httpx.AsyncClient(...)` 构造搜索无命中。
- `httpx lint OK`
- `check_no_internal_async: 8 files clean`

在 `novaic-agent-runtime` 执行：

```bash
pytest -q \
  tests/test_pr340_action_engine_effect_boundaries.py \
  tests/test_pr340_worker_effect_plan.py \
  tests/test_pr193_activity_projection.py
```

结果：`18 passed in 0.13s`。

## Conclusion

Queue FSM/worker 主路径的显式依赖边界已经清楚：clock/id/client/effect executor 都从边界注入；side effects 集中在 effect adapters / durable outbox dispatcher。

## Remaining Gaps

- `novaic_cortex.registry.WorkspaceRegistry` 仍在构造器中默认读取 env-derived `BlobPayloadPolicy.from_env()`，且默认 `clock=time.time`。这不是 Queue FSM 活路径，但不符合最极致的显式边界；更好做法是在 `main_cortex.py` startup boundary 解析 policy/clock 后显式传入。
- `HttpBlobPayloadClient.from_env()` 存在但当前 production registry 没用；它属于可疑残留 factory，需要决定保留为测试/utility 还是删除。
- `HealthRecoveryEffectAdapter` 内部持有 lazy `_client` 缓存，已被隔离在 effect adapter 内，当前可接受；如果追求完全 stateless worker effect，也可以改成外部注入 client factory。
