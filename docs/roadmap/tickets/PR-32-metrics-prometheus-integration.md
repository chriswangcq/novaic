# PR-32 统一可观测性：Prometheus Metrics 落地兜底

| 字段 | 值 |
| --- | --- |
| **Phase** | Cleanup / Backlog |
| **Milestone** | M1 尾声 |
| **Status** | `[ ]` |
| **Depends on** | PR-06, PR-07, PR-08, PR-10 |
| **PR 标题** | `chore(observability): integrate prometheus_client and implement delayed metrics` |

## 1. 目标

在先前的 PR 开发过程中，为了避免在未引入 `prometheus_client` 基础库的子仓库（如 `novaic-common`）中强行引入依赖而导致的隐患，我们将多处指标采集（Metrics）标记为了 `[-]` 延后处理。
本 PR 旨在通过系统性地引入 `prometheus_client`，并一揽子补齐由于依赖缺失而遗留的核心黄金指标（Golden Signals），保证全链路的 Observability。

## 2. 待清理指标清单 (Metrics Backlog)

以下是在过往 PR 中明确推迟，且必须在本 PR 中落地的具体指标：

### 来自 PR-06 (Caller Middleware)
- [ ] `internal_requests_total{caller, target, status}` counter：记录内部微服务之间调用的频次和状态码。

### 来自 PR-07 (Agent Owner Endpoint)
- [ ] `agent_owner_lookup_total{result="hit"|"miss"}` counter：记录 Business 端暴露的 owner 检查接口的命中与穿透情况。

### 来自 PR-08 (Ownership Resolver)
- [ ] `ownership_resolver_total{result="hit"|"miss"|"error"}` counter：记录 Resolver 请求 Business 并缓存过程中的缓存命中率与错误率。
- [ ] `ownership_resolver_latency_seconds` histogram：记录 Resolver 解析所有权的耗时分布。

### 来自 PR-10 与 PR-11 (Dispatch Assembler)
- [ ] `dispatch_total{trigger_type, result="ok"|"no_owner"|"queue_400"|"queue_5xx"|"network"}` counter：多维度的 dispatch 请求量与各类错误量监控。
- [ ] `dispatch_latency_seconds{trigger_type}` histogram：记录 Assembler 完成 assemble 与发包的全链路耗时。
- [ ] `dispatch_failed_total{caller="business"}` counter (PR-11)：记录 Fire-and-Forget 模式下的无声发包失败（Silent failure），防止消息孤儿现象。

### 来自 PR-14 (Message Outbox)
- [ ] `outbox_enqueued_total{trigger_type}` counter：每次同事务 INSERT message_outbox 时打一次。
- [ ] `outbox_backlog_count` gauge：周期性 `COUNT(*) WHERE delivered_at IS NULL`，由 subscriber 或 scheduler 定时刷新。

### 来自 PR-16 (Dispatch Subscriber)
- [ ] `subscriber_delivered_total{trigger}` counter：记录 subscriber 成功消费的数量。
- [ ] `subscriber_failed_total{kind}` counter：记录 subscriber 发生 permanent 错误的数量。
- [ ] `subscriber_retry_total{kind}` counter：记录 subscriber 发生 transient 错误的重试数量。
- [ ] `outbox_lag_seconds` gauge：记录最老的未消费消息的时间延迟。
- [ ] `outbox_claim_batch_size` histogram：记录每次 claim 捞起的行数分布。

## 3. 实施 Checklist

- [ ] 在 `pyproject.toml` 或依赖配置中合理引入 `prometheus_client` 到所需模块（如 `novaic-common` 和 `novaic-business`）。
- [ ] 封装一个共用的 Metrics Registry / Singleton（如 `common.utils.metrics`），避免多例实例化冲突。
- [ ] 在对应的源码位置恢复上述指标的 `inc()` 和 `observe()`。
- [ ] 检查 `/metrics` 接口是否能正常暴露上述数据。
- [ ] 更新对应的 Grafana 仪表盘（可选）。
