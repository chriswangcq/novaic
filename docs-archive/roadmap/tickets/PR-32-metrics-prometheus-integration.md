# PR-32 统一可观测性：Metrics 兜底落地（零依赖路径）

| 字段 | 值 |
| --- | --- |
| **Phase** | Cleanup / Backlog |
| **Milestone** | M1 尾声 |
| **Status** | `[x]` 2026-04-21 落地（零依赖方案，未引入 `prometheus_client`） |
| **Depends on** | PR-06, PR-07, PR-08, PR-10, PR-14, PR-16 |
| **PR 标题** | `chore(observability): land delayed golden-signal metrics via zero-dep registry` |

## 1. 目标与方案选择

在 PR-06 / PR-07 / PR-08 / PR-10 / PR-11 / PR-14 / PR-16 的开发过程中，为避免在尚未引入 `prometheus_client` 依赖的子仓（特别是 `novaic-common`、Entangled）中强行拉库，共有 13 个黄金信号指标被标 `[-]` 延后。本 PR 负责一次性补齐。

原 ticket 的字面方案是"引入 `prometheus_client`"，落地时改为**零依赖**方案，原因：

1. **已有样板**：`novaic-cortex/novaic_cortex/observability.py`（P3-7）早已实现了一套 thread-safe、直接吐 Prometheus exposition text format 的 in-process registry（~100 LOC）。其头部注释即写明：_If someone later wants full `prometheus_client` semantics, swap the internals; the call sites stay._
2. **调用点空集**：全仓 `rg` 13 个目标 metric 名 → 仅 ticket 自身匹配，**零生产调用点**。真正的工作量在 call sites + 统一 registry，不在引入 library。
3. **架构原则"系统简单"**：引 `prometheus_client` 意味着 (a) 4 个子仓都要新增依赖；(b) Cortex 既有实现必须推翻重写；(c) 子进程型 worker（`main_subscriber.py`）要么起多端口，要么踩 `PROMETHEUS_MULTIPROC_DIR` 文件目录共享的坑。
4. **可回退**：公共 API（`metric_inc` / `metric_observe` / `metric_set` / `metric_timer` / `render_metrics`）与 `prometheus_client` 的心智模型对齐。如果未来需要真直方图 / exemplars / remote write，替换模块内部即可，call sites 不动。

## 2. 实施细节

### 2.1 公共 registry

- 新增 `novaic-common/common/utils/metrics.py`：counter / gauge / summary + `metric_timer` 上下文管理器 + `start_metrics_http_server` 子进程 exposition helper + `reset_all_metrics_for_tests`。单 `threading.Lock` 保护三张 dict（counters / gauges / histograms），labels 按 sorted-tuple key 归一化。
- 新增 `Entangled/packages/server-python/entangled/metrics.py`：镜像上面的公共 API。Entangled 是 foundation package 不可 import `novaic-common`（见 `entity_store.py` 头部注释），所以需要物理重复这一份文件。两处改动要对照同步（头部注释要求）。
- `novaic-cortex/novaic_cortex/observability.py`：删除本地实现，改为 `from common.utils.metrics import *`；保留 Cortex-specific 的 `log_cortex()`（INFO 结构化日志 + 已知事件 → counter 自动 bump）。

### 2.2 Call site 接入一览

| Metric | 类型 | 接入位置 | Label 形状 |
| --- | --- | --- | --- |
| `internal_requests_total` | counter | `common/http/clients.py::_record_internal_request`（response event-hook） | `{caller, target, status}` |
| `agent_owner_lookup_total` | counter | `business/internal/agent.py::get_owner` | `{result=hit\|miss}` |
| `ownership_resolver_total` | counter | `common/agents/ownership.py::resolve_sync` | `{result=hit\|miss\|error}` |
| `ownership_resolver_latency_seconds` | summary | 同上（miss/http 路径） | `{}` |
| `dispatch_total` | counter | `common/wake/assembler.py::_parse_dispatch_response`（ok/queue_400/queue_5xx）+ `assemble_sync`（no_owner）+ `dispatch_sync`（network） | `{trigger_type, result=ok\|no_owner\|queue_400\|queue_5xx\|network}` |
| `dispatch_latency_seconds` | summary | `common/wake/assembler.py::dispatch_sync` | `{trigger_type}` |
| `dispatch_failed_total` | counter | `business/subscribers/dispatch_subscriber.py`（permanent 分支） | `{caller="business-subscriber"}` |
| `outbox_enqueued_total` | counter | `entangled/sql/entity_store.py::append`（co-tx insert 后） | `{trigger_type}` |
| `outbox_backlog_count` | gauge | `business/subscribers/dispatch_subscriber.py::_claim_batch`（每 tick） | `{}` |
| `outbox_lag_seconds` | gauge | 同上（由新 ClaimResponse 字段派生） | `{}` |
| `outbox_claim_batch_size` | summary | 同上 | `{}` |
| `subscriber_delivered_total` | counter | subscriber 成功 dispatch 分支 | `{trigger}` |
| `subscriber_failed_total` | counter | subscriber permanent 分支（含 malformed payload / DispatchError / httpx.HTTPError） | `{kind}` |
| `subscriber_retry_total` | counter | subscriber transient 分支 | `{kind}` |

`dispatch_failed_total` 在 PR-11 原设计里对应 Business `_dispatch_trigger` 的 fire-and-forget 静默失败。PR-18 已删除该函数，入口改到 subscriber permanent 分支，但指标名保持不变（`caller` label 由 `business` 改为 `business-subscriber`，以明示工作节点变迁）。

### 2.3 Outbox 统计 piggy-back

为让 subscriber 每 tick 能无额外 round-trip 更新 `outbox_backlog_count` / `outbox_lag_seconds` gauge，`/v1/outbox/claim` 的 `ClaimResponse` 扩展了两个字段：

```python
backlog_count: int = 0             # COUNT(*) WHERE delivered_at IS NULL
oldest_pending_age_ms: int = -1    # now - MIN(created_at); -1 哨兵 = 无 pending
```

扩展字段都是 `int = default`，对旧 client 向后兼容（pydantic 额外字段默认被忽略）。scalar SELECT 在 claim 的同一 `db.transaction("global")` 内完成，保证 subscriber 看到的 backlog 与 claim 之后的 pending 状态一致。

### 2.4 Exposition endpoints

| 服务 | 路由 | 实现 |
| --- | --- | --- |
| Entangled | `GET /metrics` | `factory.py` 末尾注册，unauth，返回 `PlainTextResponse(render_metrics(), 'text/plain; version=0.0.4')` |
| Business | `GET /metrics` | `main_business.py` 顶层 app，实现同上 |
| Cortex | `GET /metrics` | `novaic_cortex/api.py` 早已存在（P3-7） |
| Subscriber (subprocess) | `http://127.0.0.1:19985/metrics` | `main_subscriber.py` 启动时调 `start_metrics_http_server(args.metrics_host, args.metrics_port)` 拉 daemon 线程的 `ThreadingHTTPServer`；`--metrics-port` / `--metrics-host` CLI 可覆盖；bind 失败 → 启动期 crash（loud fail）。`subscriber.run()` 退出时 `metrics_server.shutdown()` 释放 FD |
| Health Worker (subprocess) | `http://127.0.0.1:19984/metrics` | `main_novaic.py::run_health` 同上；TD-5（2026-04-21）新增 — 暴露 `orphans_total{severity}` + assembler-side `dispatch_total` |
| Scheduler Worker (subprocess) | `http://127.0.0.1:19983/metrics` | `main_novaic.py::run_scheduler` 同上；TD-5（2026-04-21）新增 |

FastAPI 服务 `/metrics` 不走 auth（scrape 默认 on-host，端口也 bind 到私网接口）；若未来要暴露到公网，再加 IP allowlist 中间件。

### 2.5 测试

- `novaic-common/tests/test_metrics.py`（8 cases）：counter / gauge / summary round-trip；label 顺序归一化；`metric_timer` 正延时；`reset_all_metrics_for_tests` 全清零；8 线程 × 500 次并发自增正确求和。
- `novaic-common/tests/test_metrics_http_server.py`（2 cases）：`start_metrics_http_server` 真起 socket；GET /metrics 返回与直接 render_metrics() 一致；未知路径 404。
- 既有 `novaic-common`（86 pass）/ `novaic-business`（subscriber + internal agents 26 pass）/ `novaic-cortex`（scope_state + log 24 pass）全绿。
- 预先存在的失败（`test_message_trace.py::test_claimed_with_scope_composes_cortex_meta` 连 Entangled 被拒、`test_outbox_endpoints.py` FakeDatabase 缺 `.transaction()`、`test_workspace.py` MemoryStore 行为）不在本 PR 范围。

## 3. 采集 / 消费

零流量生产环境下，所有 counter 长时间停在 0 属于正常信号（meaning: 没有用户消息落库）。真正"有流量但 counter 不动"才是 bug —— 这正是引入 metric 的目的。

Runbook 侧不强制配 Prometheus server；ops 可以先用：

```bash
curl -s http://127.0.0.1:19900/metrics | rg '^(internal_requests|dispatch_total|outbox_)' 
curl -s http://127.0.0.1:19985/metrics | rg '^subscriber_'
```

当流量恢复后，如需实时可视化再配 Prometheus 抓取 + Grafana dashboard，届时 call sites 零改动。

## 4. 回滚

- 反向顺序 revert：(a) Business `/metrics` 路由 + subscriber http.server (b) Entangled `/metrics` 路由 + entity_store `metric_inc` (c) 各 call site 的 `metric_inc`/`metric_timer` (d) `common/utils/metrics.py` + `entangled/metrics.py` 文件删除 + cortex observability 还原本地实现。
- Cortex `log_cortex()` 行为在回滚后保持不变（它的 `metric_inc` 调用会重新指向本地实现），`cortex_*` counter 指标不丢。
- 未扩展的 `ClaimResponse.backlog_count` / `oldest_pending_age_ms` 默认 0/-1，旧 subscriber client 能安全读取（pydantic 忽略新字段）。
