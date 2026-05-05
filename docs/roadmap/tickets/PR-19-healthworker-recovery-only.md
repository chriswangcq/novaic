# PR-19  HealthWorker → recovery-only（删 `_scan_unhandled_messages`）

> Historical ticket archive: this file records a closed or retired implementation path. It is not current architecture or active backlog; use the ticket index and current architecture docs as the source of truth.


| 字段 | 值 |
| --- | --- |
| **Phase** | 2 |
| **Milestone** | M2 |
| **承诺** | R1 + R5 |
| **Status** | `[x]` (merged; see roadmap README index) |
| **Depends on** | PR-17 |
| **Blocks** | PR-26 |
| **估时** | 0.5 d |
| **Owner** | __ |
| **PR 标题** | `refactor(runtime): HealthWorker recovery-only; rename → recovery_worker` |

## 目标

删掉 HealthWorker 扫未处理消息并再发 dispatch 的职责（该职责已由 subscriber 承担）。HealthWorker 降级为 "任务/saga 超时回收" 的 recovery 组件。重命名文件/类清晰表达语义。

## 范围

- `novaic-agent-runtime/task_queue/workers/health_worker_sync.py` → `recovery_worker_sync.py`
- 类名 `HealthWorkerSync` → `RecoveryWorkerSync`
- worker 注册处（`workers/__init__.py` 或 main）

## 前置 Checklist

- [archived] PR-17 合并且观察期过
- [archived] PR-18 合并
- [archived] subscriber 主路径稳定运行 ≥ 24h

## 实施 Checklist

### 删除代码

- [archived] 删 `_scan_unhandled_messages`（整段）
- [archived] 删相关辅助方法（`/internal/messages/unread-grouped` 的调用等）
- [archived] 删硬编码的 dispatch 逻辑

### 保留并改名

- [archived] 保留 `_perform_check` 的 `/api/queue/recover/all` 调用（孤儿 task/saga 回收）
- [archived] 重命名：
  ```
  health_worker_sync.py   → recovery_worker_sync.py
  class HealthWorkerSync  → class RecoveryWorkerSync
  ```
- [archived] 调用方同步改
- [archived] log prefix 从 `health` 改为 `recovery`

### Env / CLI

- [archived] 如果有 `HEALTH_WORKER_ENABLED` 之类的环境变量，保留语义（不重命名），或增加 `RECOVERY_WORKER_ENABLED`（建议新名）
- [archived] `scripts/start.sh` 对应更新

### PR-26 占位

- [archived] 在 `recovery_worker_sync.py` 顶部加 TODO 注释：`# TODO(PR-26): add orphan emitter for outbox-pending > threshold`

## 测试 Checklist

- [archived] 人为制造一个孤儿 saga（dispatch 后 worker kill）→ `/recover/all` 接管，saga 恢复
- [archived] 人为制造一条 "主路径失败" 消息（外部工具把 subscriber 关掉，写 outbox）→ 此 PR 合并后，没有兜底会让消息积压（PR-26 填坑）
- [archived] 日志里不应再出现 `Fallback dispatch failed` / `user_id is required`

## 可观测性 Checklist

- [archived] metric 重命名：`healthworker_scan_total` → `recoveryworker_recover_total`（或保留旧名并 deprecate）
- [archived] 启动日志：`recovery_worker starting`

## 文档 Checklist

- [archived] [message-wake-refactor.md](../message-wake-refactor.md) P2-5 → `[x]`
- [archived] 本工单 Status → `[x]`
- [archived] `docs/runtime/README.md` 里 "Watchdog / HealthWorker" 一节更名
- [archived] PR-03 allowlist 删除 `health_worker_sync.py`
- [archived] PR-04 allowlist 删除相关裸 client 条目（PR-12 已迁，但文件已重命名）

## 验收命令

```bash
rg '_scan_unhandled_messages' novaic-agent-runtime/
# 预期：空

rg 'HealthWorkerSync' novaic-agent-runtime/
# 预期：仅 tests 或 migration 说明

# 启动后日志
tail -f recovery.log | rg 'recovery_worker starting'
```

## 回滚

- revert 本 PR → HealthWorker + `_scan_unhandled_messages` 回来；此时 subscriber 依然是主路径，HealthWorker 再做 dispatch 会被 Queue Service idempotency ledger 吃掉重复。

## 备注

- 本 PR 后"主路径由 subscriber、recovery 由 RecoveryWorker" 的职责划分对齐 R1。
- PR-26 会在此基础上加 orphan emitter（不是 re-dispatch，是告警）。
- 不要在本 PR 里加 emitter，拆开更清晰。
