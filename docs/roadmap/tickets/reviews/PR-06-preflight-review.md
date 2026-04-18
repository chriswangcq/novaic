# PR-06 调研 Review + 三决策裁决 + 5 条补充

> 被审对象：[`PR-06-preflight-antigravity.md`](PR-06-preflight-antigravity.md)
> Ticket：[`../PR-06-services-consume-caller-header.md`](../PR-06-services-consume-caller-header.md)
>
> **结论：**
> - ✅ 5 服务中间件现状识别对
> - ✅ 三个决策点都问在了真正的关键位置
> - ⚠️ 报告深度不如 PR-05 v2（缺 file:line、缺测试表、缺 log 格式 SSOT、缺范围边界），不过不是 blocking
> - **拍板后直接进 T1，但 T1 时要把 §A 补的 5 条一起落**

---

## A. 三个决策的裁决（直接按这个做）

### Q1：统一 Middleware vs 分散实现？→ **批 A：统一放 novaic-common**

**裁决**：在 `novaic-common/common/middlewares/caller_logging.py` 创建一个可挂载的 middleware 工厂，5 个服务的 `main_*.py` 各一行挂载。

**为什么不是 B（分散）**：PR-06 的**核心价值就是跨服务 log 格式一致**——只有格式一致，ELK/grep 才能 join `caller=X`。分散实现两周内必漂移，直接违反 PR 目标。

**落地形态**（你照用）：

```python
# novaic-common/common/middlewares/caller_logging.py
from fastapi import Request, FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time

_logger = logging.getLogger("novaic.access.internal")

INTERNAL_PATH_PREFIXES_DEFAULT = ("/internal/", "/api/queue/", "/api/cortex/")

class CallerLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, service_name: str, internal_path_prefixes=None):
        super().__init__(app)
        self.service_name = service_name  # 本服务自己的名字
        self.prefixes = internal_path_prefixes or INTERNAL_PATH_PREFIXES_DEFAULT

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        is_internal = any(path.startswith(p) for p in self.prefixes)

        caller = request.headers.get("X-Internal-Service") or ""
        has_key = bool(request.headers.get("X-Internal-Key"))

        if not caller:
            caller = "unknown"
            if has_key and is_internal:
                _logger.warning(
                    "internal_caller_unknown path=%s method=%s target=%s",
                    path, request.method, self.service_name,
                )

        # 同进程异步调用透传用：contextvar
        from common.log_context import caller_var
        token = caller_var.set(caller)
        request.state.caller = caller

        t0 = time.time()
        try:
            response = await call_next(request)
        finally:
            caller_var.reset(token)

        if is_internal:
            duration = time.time() - t0
            _logger.info(
                "internal method=%s path=%s status=%s caller=%s target=%s duration=%.3fs",
                request.method, path, response.status_code,
                caller, self.service_name, duration,
            )
        return response

def install_caller_middleware(app: FastAPI, *, service_name: str, **kwargs):
    app.add_middleware(CallerLoggingMiddleware, service_name=service_name, **kwargs)
```

每服务 `main_*.py`：

```python
from common.middlewares.caller_logging import install_caller_middleware
install_caller_middleware(app, service_name="business")  # / cortex / queue / gateway / device
```

---

### Q2：Business / Gateway / Device 是否顺便补 `X-Internal-Key` 拦截？→ **不做**

**裁决**：PR-06 **只做 caller 提取 + access log**，不做 key 拦截。

**理由**：
1. Ticket §实施 第 2 条明确："**不做 401**（灰度期）"。PR-06 不是安全加固 PR。
2. 添加 key 拦截基础设施涉及：env var 来源 (`BUSINESS_INTERNAL_KEY`? 还是统一 key?)、哪些路径豁免、测试覆盖——是独立 PR 的体量。
3. 这三个服务内部端点现状**确实**是开的，是独立的安全洞——**已记 tech-debt**"内部 Key 未统一"（PR-05 裁决时留下的）。等那个 tech-debt 处理时一起做。
4. 塞进 PR-06 会让本 PR 爆炸半径失控，重蹈 PR-05 T1 覆辙。

**调研报告里要补一句**：`## 范围收窄决议`（沿用 PR-05 v2 §5 的体例），明确写清"本 PR 不引入 X-Internal-Key 拦截"。

---

### Q3：RPC 透传要不要改 Task/Saga payload DB schema？→ **不改 schema**

**裁决**：**只在 log 里透传，不 persist**。

**具体怎么做**：

1. **创建 Task/Saga 时**：在 Queue Service 的 `POST /api/queue/tasks`（或等价路由）handler 内，读 `request.state.caller`，`_logger.info("task_created id=%s caller=%s ...")`——只打 log，不落库。
2. **Worker 执行时**：worker 进程有自己的 `service_name`（PR-05 已定：`runtime-task` / `runtime-scheduler` / `runtime-saga`）。打 log 时 `caller=<worker_service_name>`，和 `task_id` 一起出现即可。
3. **跨进程 trace 查询**：通过 `task_id` join 两条 log。不需要数据库字段。

**为什么不持久化**：
- 真正的"跨进程 trace caller"是 R4（scope trace）的范畴，**PR-20 / PR-24 专门做**（`LogContext` contextvar + `scope.inputs[]` + `message.claimed_by_scope`）
- 提前在 task payload 加 `caller` 列，等 PR-20 来的时候要么重复、要么冲突，不如不做

**调研报告里要补一句**：本 PR 不改 DB schema；跨进程 caller 传播留给 PR-20 / PR-24。

---

## B. 我要额外补的 5 条（T1 时一起落）

### B.1 `ContextVar` 是关键，不是 `request.state` 独占

`request.state.caller` 只在单个 HTTP request 的生命周期内存在。但 ticket §"服务内部 RPC 分摊"要求跨**同进程异步调用**也要带 caller（比如 business handler 内部再 await 一个子任务）。

解法：**同时**用 `contextvars.ContextVar` 和 `request.state`，两者都写。

```python
# novaic-common/common/log_context.py
from contextvars import ContextVar
caller_var: ContextVar[str] = ContextVar("caller", default="unknown")
```

这个 file 现在就创建（只有一行），**PR-24 会扩展进 LogContext**（绑 scope_id / agent_id / user_id）。这一步做了就能让 PR-24 无缝扩展，不做的话 PR-24 要重构。

### B.2 Log 格式定稿 — SSOT

5 个服务必须用**同一个 key=value 格式**：

```
internal method=<GET/POST> path=<str> status=<int> caller=<str> target=<str> duration=<float>s
```

- `target` = 本服务自己的 `service_name`（让日志里 "谁调我" 和 "我是谁" 都清楚）
- 纯 `key=value` 格式，**不搞 JSON**（一开始就 JSON 会让本地 `tail -f` 难读；后续 ELK 再做解析）
- Log level = `INFO`
- Logger name = `novaic.access.internal`

这个格式**就是上面 §A Q1 代码给的那个**。不要改格式。

### B.3 Ticket 范围是 5 个服务，但你漏列了 4 个

仓库里有 FastAPI 的服务比 ticket 列的多：

```
novaic-llm-factory/factory/app.py    ← FastAPI
novaic-mcp-vmuse                     ← 需核实
novaic-quic-service                  ← 需核实
novaic-storage-a                     ← 需核实
```

**本 PR 仍按 ticket 做 5 个**（cortex / queue / business / gateway / device），但在 T1 时你要：
- [ ] 核实上述 4 个服务是否是 FastAPI / 是否有 internal 端点
- [ ] 在调研文档末尾加一节 `## 延后项`：列出这 4 个，说明"和 ticket 范围一致不纳入"；建议开 PR-06.5 follow-up ticket
- [ ] 顺便确认一下 PR-05 的 `service_name` 列表里是否需要加 `llm-factory` / `storage` / ...（PR-05 当时定了 7+2 个：`business/cortex/gateway/device/runtime-task/runtime-scheduler/runtime-health/runtime-saga/common-auth`）

### B.4 `queue_service/main.py` 有 `uvicorn access_log=True` — 避免双重 log

```
novaic-agent-runtime/queue_service/main.py:268
    access_log=True,
```

uvicorn 自己会打一条 access log（不含 caller）。我们的 middleware 又打一条（含 caller）。结果每个内部请求在 log 里出现两次。

**推荐做法**：
- **不关** uvicorn 的（避免改动面扩大 + 保留 uvicorn 原有 client_ip 等字段）
- 我们的 middleware 只在 **internal_path 命中时** 打 log（§A 的代码已经这么写了 `if is_internal`）
- 本地 `tail` 时用 `rg 'internal '` 就能过滤出我们自己的那条

T1 验证时留意：如果仍觉得吵，再考虑关 uvicorn 的。

### B.5 测试 Checklist（你的报告里没展开）

最少要写 3 类测试：

**单元测**（每服务一份，放 `tests/test_caller_middleware.py`）：
```python
def test_middleware_extracts_caller(client):
    resp = client.get("/internal/health", headers={
        "X-Internal-Service": "test-x",
        "X-Internal-Key": "dev",
    })
    # 断言 request.state.caller == "test-x"
    # 可以通过在 app 里注册一个 /internal/whoami 测试路由，返回 request.state.caller 验证

def test_middleware_unknown_caller_warns(client, caplog):
    client.get("/internal/health", headers={"X-Internal-Key": "dev"})
    assert "internal_caller_unknown" in caplog.text

def test_middleware_nonpath_skipped(client, caplog):
    client.get("/public/ping", headers={"X-Internal-Service": "test-x"})
    assert "internal method=" not in caplog.text  # 不应该打 internal log
```

**集成测（手工即可）**：
- 启所有服务 → curl 带 `X-Internal-Service: cortex` 调 business `/internal/agents/<id>/owner`
- `tail -f business.log | rg 'caller=cortex'` 必须看到
- 无 header curl → 必须看到 `caller=unknown` + WARN

**contextvar 透传测**：
- 在 middleware 里 set 后，在 handler 里 `import caller_var; assert caller_var.get() == "test-x"`

---

## C. T1 前要补的 3 件小事（5 分钟能搞定）

在调研文档 v2 里加上：

1. **§范围收窄决议**（抄 PR-05 v2 §5 格式）——明确 Q2 不做 key 拦截、Q3 不改 schema
2. **§Log 格式 SSOT**——抄 §B.2 的那一行
3. **§延后项**——抄 §B.3 的四个服务列表

改完直接进 T1，不需要再 review。

---

## D. T1 阶段硬约束（记一下，PR-05 血泪）

1. **每个 submodule + 主仓 declare done 前 `git status` 确认空行**（PR-05 连续栽两次的地方）
2. **单元测必须真跟 git**（不能 `?? test_xxx.py` untracked）
3. **log 格式 5 个服务保持字面一致**，不要某个服务创新
4. **Ticket §Scope 列的 5 个服务都要做**（不要只做 3 个就说完成）
5. **commit 分拆**：
   - novaic-common: `feat(common): caller_logging middleware + log_context (PR-06)`
   - novaic-cortex: `feat(cortex): install caller middleware (PR-06)`
   - novaic-agent-runtime: `feat(queue): install caller middleware (PR-06)`
   - novaic-business: `feat(business): install caller middleware (PR-06)`
   - novaic-gateway: `feat(gateway): install caller middleware (PR-06)`
   - novaic-device: `feat(device): install caller middleware (PR-06)`
   - main repo: `chore: bump submodules for PR-06`

---

## E. 验收命令（PR 描述粘这个）

```bash
# 1. middleware 挂载成功（5 服务 smoke）
for svc in cortex queue business gateway device; do
  curl -s -o /dev/null -w "%{http_code} " \
    -H "X-Internal-Service: smoke-test" -H "X-Internal-Key: $NOVAIC_INTERNAL_KEY" \
    http://localhost:${PORT[$svc]}/internal/health
done
# 每个服务 log 出现 caller=smoke-test

# 2. 无 caller 告警
curl -H "X-Internal-Key: $NOVAIC_INTERNAL_KEY" http://localhost:7000/api/queue/sessions
grep internal_caller_unknown queue-service.log  # 必须有

# 3. lint 保持 green
bash scripts/ci/lint_httpx.sh && bash scripts/ci/lint_dispatch.sh

# 4. 单测
pytest novaic-common/tests/test_caller_middleware.py -v
# 至少 3 条 pass

# 5. submodule 干净
for d in novaic-common novaic-cortex novaic-agent-runtime novaic-business novaic-gateway novaic-device; do
  (cd $d && git status --short | wc -l) # 每个都 0
done
```

---

## F. 整体评语

这份调研比 PR-05 v2 薄，但**问题问对了地方**——Q1/Q2/Q3 都是真决策点，不是凑数。这说明你已经学会"识别拐点"而不是"照搬 ticket"。

薄的地方（缺 file:line 表、缺测试 list、缺 log 格式 SSOT）是能力曲线上一个正常缺口，我在 §B 里替你补了。下一张 PR（PR-07 或 PR-08）调研时，请**主动包含这四项**：
- 具体文件 + 行号表
- 测试 checklist（单元 / 集成 / 负测 各至少 1 条）
- 关键字段/格式 SSOT
- 范围边界（做什么、不做什么、以及延后做什么）

---

## G. 可以开工

按 §A 三裁决 + §B 五补充 + §C 三小事 + §D 五硬约束 执行。

不需要再交第二版调研给我看——T1 完工后直接按 §E 的 5 条验收命令出结果。

**记得 declare done 前跑 `git status`。**

— Reviewer
