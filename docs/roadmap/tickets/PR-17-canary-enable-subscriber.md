# PR-17  灰度开启 dispatch_subscriber（canary，观察 24-48h）

| 字段 | 值 |
| --- | --- |
| **Phase** | 2 |
| **Milestone** | M2 |
| **承诺** | R1 |
| **Status** | `[x]` (deployed 2026-04-19; bake gate revoked — see `reviews/bake-gate-abandonment-2026-04-19.md`) |
| **Depends on** | PR-16 |
| **Blocks** | PR-18, PR-19 |
| **估时** | 0.5 d（+ 24–48h 观察） |
| **Owner** | __ |
| **PR 标题** | `chore(business): enable dispatch_subscriber by default (canary)` |

## 目标

把 flag 翻成 on，subscriber 正式参与主路径；HealthWorker 仍在跑作为兜底；双路径并行 24–48h 观察稳定性。

## 范围

- `novaic-business/main_business.py`：新增 `--enable-subscriber` CLI flag（取代旧 `DISPATCH_SUBSCRIBER_ENABLED` env，环境变量保留作本地兜底）
- `scripts/start.sh`：新增 `NOVAIC_ENABLE_SUBSCRIBER` / `NOVAIC_HEALTH_CHECK_INTERVAL` 环境入口
- `scripts/deploy-business.sh`：首发（`--first-time`）+ 日常增量双模式部署脚本
- `scripts/canary/traffic.py`：bootstrap / send / observe / watch 四合一 canary 工具
- `docs/runbooks/subscriber-canary.md`：runbook（红线 / 分阶段 / 回滚）
- `Entangled/.../outbox.py`：PR-16 follow-up — outbox 端点加 `db.transaction("global")`，修复与 `append` 并发下的 `database is locked`

## 前置 Checklist

- [x] PR-16 合并且本地已跑通（Stage 0 dry-run 于 2026-04-18 完成，10 条并发消息 0 次 `database is locked`）
- [-] 监控面板能看到 `subscriber_delivered_total` / `outbox_lag_seconds` / `healthworker_scan_total{result=ok}` → defer to PR-32；Canary 期用 runbook §Monitoring without Prometheus 的 shell 替身
- [x] 有明确回滚路径（`NOVAIC_ENABLE_SUBSCRIBER=0` 重启 Business，HealthWorker 自动承接；SLO ≤ 45s）

## 实施 Checklist

- [x] `novaic-business/main_business.py`：加 `--enable-subscriber` CLI flag；CLI 优先级高于 env；修复 PR-16 遗留的 `from common.client import` 错误 import；`outbox_client` 改为直接构造 `httpx.AsyncClient` + `X-Service-Token`（匹配 Entangled 认证）
- [x] `scripts/start.sh`：Business 启动读 `NOVAIC_ENABLE_SUBSCRIBER`，HealthWorker 读 `NOVAIC_HEALTH_CHECK_INTERVAL`
- [x] `scripts/deploy-business.sh`：`--first-time` 模式（停机 → 备份 DB → rsync → flag off 启动 → 健康检查 → 提示下一步）+ 默认增量模式
- [x] `scripts/canary/traffic.py`：bootstrap（幂等创建 canary_u_1 / canary_a_1）、send、observe、watch
- [x] `docs/runbooks/subscriber-canary.md`：红线警告（巨型集成上线）+ 4 阶段节拍 + 回滚 playbook
- [x] `Entangled/.../outbox.py`：claim / mark_delivered / mark_failed 包一层 `db.transaction("global")`，与 `append` 串行化，消除 SQLite 写锁冲突
- [ ] 生产重启 Business → 日志应当看到 `dispatch_subscriber enabled`（Phase 2，待发车）

## 观察期 Checklist（24–48h）

### 健康指标

- [ ] `outbox_lag_seconds` P99 < **2 s**
- [ ] `subscriber_delivered_total` 与主路径消息数接近 1:1
- [ ] `subscriber_failed_total{kind=no_owner}` 为 0（若 >0，表 agent 数据有问题，需单独处理）
- [ ] `subscriber_retry_total` 占比 < 1%
- [ ] `healthworker_scan_total{result=ok}` 依然能跑（兜底仍有效）
- [ ] `healthworker_scan_total{result=ok}` 的 "真正 re-dispatch" 次数应 → 0（主路径已接管）

### 对照

- [ ] grep `event=dispatch` 日志里 `via=assembler` 出现的 caller：应**主要**是 `business-subscriber`；`runtime-health` 应 → 0

### 红线（触发即回滚）

- [ ] outbox 堆积超过 1000 行持续 > 5 min
- [ ] `outbox_lag_seconds` > 10s 持续
- [ ] 用户侧"消息不回复"投诉增加

## 测试 Checklist

- [ ] 预发环境：发 10 条不同 trigger 的消息 → 全部 delivered_at 填上
- [ ] 故意把 subscriber kill → HealthWorker 接管（证明兜底还在）
- [ ] subscriber 恢复 → outbox 积压清空

## 可观测性 Checklist

- [ ] 新建或更新 dashboard panel：
  - 主路径 dispatch rate (subscriber)
  - 兜底路径 dispatch rate (HealthWorker)
  - outbox_lag_seconds p50/p99
  - subscriber_failed_total by kind

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) P2-3（gating 说明）→ `[x]`
- [ ] 本工单 Status → `[x]`
- [ ] 在 `HANDOVER.md` 记录 "dispatch_subscriber 上线时间 / 观察起止时间"

## 验收命令

```bash
# 观察窗口结束后
curl -s localhost:8200/metrics | rg 'subscriber_delivered_total'
curl -s localhost:8200/metrics | rg 'healthworker_scan_total.*result="ok"'
# 比例：subscriber / healthworker-redispatch >> 99%
```

## 回滚

1. `DISPATCH_SUBSCRIBER_ENABLED=0`
2. 重启 Business
3. HealthWorker 自动承接（PR-12 已让它能工作）

## 备注

- 本 PR 是 Phase 2 的"分水岭"：合并后主路径由 subscriber 承担，HealthWorker 降为兜底。
- PR-18 / PR-19 在观察期过后才能启动。
