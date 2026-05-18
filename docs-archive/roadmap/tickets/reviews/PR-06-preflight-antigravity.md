# PR-06 Preflight Report (X-Internal-Service Auth & Logging)

## 1. 调研目标
识别所有后端服务的认证中间件/依赖点，制定 `X-Internal-Service` 头解析和 Access Log 归因机制的具体实施方案，确保满足 PR-06 规范。

## 2. 现状分析 (Where to inject)

### A. Cortex (`novaic-cortex/novaic_cortex/api.py`)
- **现状**: 存在 `@app.middleware("http") _internal_key_middleware`。
- **改动**: 在此中间件中提取 `X-Internal-Service`。如果是 internal 路径，附加 `request.state.caller = caller`，并在后续执行完毕后打印 access log (`method=... path=... status=... caller=... internal=1`)。对于 `X-Internal-Key` 存在但缺失 `X-Internal-Service` 的情况，打印 WARN。

### B. Queue Service (`novaic-agent-runtime/queue_service/main.py`)
- **现状**: 存在 `@app.middleware("http") _queue_internal_key_middleware`。
- **改动**: 同上，读取并注入 `request.state.caller`。记录自有的 access log，缺失 service 时报警。

### C. Business (`novaic-business`)
- **现状**: 内部 API 路由定义在 `business/internal/__init__.py`。并没有全局的 internal_key 中间件，也未找到 ticket 预期的 `business/internal/auth.py`。
- **改动**: 建议在 `main_business.py` 中新增一个全局的 logging / caller extraction 中间件；或专门创建 `business/internal/auth.py` 存放 internal 专属依赖（通过 `Depends` 或 Router Middleware），负责解析 `X-Internal-Service` 及补充 access log。

### D. Gateway (`novaic-gateway/gateway/infra/auth.py`)
- **现状**: `validate_token` 供 Nginx auth_request 调用。Nginx 代理时也可以附加 logging 字段。
- **改动**: 在 Gateway Python 服务层面，可以在 `main_gateway.py` 添加一个全局 access log 中间件，并在内部通信验证时进行 caller 解析和 WARN 校验。

### E. Device (`novaic-device`)
- **现状**: 内部端点在 `internal_vm_routes.py` 等。目前没有全局 `X-Internal-Key` 拦截中间件。
- **改动**: 在 `main_device.py` 增加全局 caller-tracking access log 中间件。

## 3. 实施方案建议

由于所有服务均使用 FastAPI，为了统一下沉日志格式和规范处理逻辑，我提议在 `novaic-common/common/middlewares.py` (若无则新建) 中封装一个通用的 `InternalCallerMiddleware`（基于 BaseHTTPMiddleware），并在所有服务的 `main.py` 中统一挂载。

```python
import logging
import time
from fastapi import Request

logger = logging.getLogger("access")

async def caller_logging_middleware(request: Request, call_next):
    start_time = time.time()
    
    # 提取 caller
    caller = request.headers.get("X-Internal-Service")
    internal_key = request.headers.get("X-Internal-Key")
    
    is_internal = bool(internal_key or caller)
    
    if not caller:
        caller = "unknown"
        if internal_key:
            logger.warning(f"internal_caller_unknown path={request.url.path} method={request.method}")

    request.state.caller = caller
    
    response = await call_next(request)
    
    # Access Log 追加
    if is_internal:
        duration = time.time() - start_time
        logger.info(
            f"method={request.method} path={request.url.path} "
            f"status={response.status_code} caller={caller} internal=1 "
            f"duration={duration:.3f}s"
        )
        
    return response
```
这不但覆盖了 PR 要求的 access log 追加，也使得代码高度复用，避免在 5 个服务中手写几乎相同的代码。

## 4. 问题与裁决请求

1. **统一 Middleware vs 分散实现**: 是否允许我在 `novaic-common` 中创建统一的 Middleware 供各服务直接挂载，还是必须严格在各服务自己的代码库里分别实现（考虑到各服务现有的 logging formatter 可能不一致）？
2. **Business / Gateway / Device 的 internal_key 拦截**: 目前这三个服务没有全局配置 `X-Internal-Key` 的检验。是否需要本 PR 仅做 `caller` 提取及 Access Log，还是顺便把它们的 `X-Internal-Key` 拦截框架（不抛 401 仅 WARN）也建立起来？
3. **RPC 分摊的透传**: Ticket 中提到 "各服务若有内部消息总线 / worker → 把 caller 也透传到 log"。Queue Service 的 `TaskQueue` 或 `SagaOrchestrator` 是否需要我把 `caller` 字段写进 Task/Saga 的 Payload DB Schema 中，以便在 worker 执行时一并取出打到 log？

请指示具体倾向，批准后我将开始实施。

## 5. 范围收窄决议
- **不做 X-Internal-Key 拦截**：本 PR 仅做 caller 提取及 Access Log，不为 Business / Gateway / Device 新增 Key 拦截（避免引入安全风险及爆炸半径扩大）。
- **不改 DB Schema**：RPC 透传仅在 log 层面实现（如 queue task_created 打印 caller），不把 `caller` 字段持久化入库。完整的跨进程 Trace 留给后续 PR-20 / PR-24 的 scope 机制处理。

## 6. Log 格式 SSOT
5 个服务必须使用统一的 key=value 格式：
`internal method=<GET/POST> path=<str> status=<int> caller=<str> target=<str> duration=<float>s`

## 7. 延后项
在代码库中发现了额外的 4 个服务：
- novaic-llm-factory/factory/app.py
- novaic-mcp-vmuse
- novaic-quic-service
- novaic-blob-service
经确认，为保持与 PR 目标一致，本 PR 不将其纳入改动范围，建议后续另开 `PR-06.5` 跟进。
