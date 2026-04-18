# PR-13  SchedulerWorker 迁到 Assembler

| 字段 | 值 |
| --- | --- |
| **Phase** | 1 |
| **Milestone** | M1 |
| **承诺** | R2 |
| **Status** | `[ ]` |
| **Depends on** | PR-10 |
| **Blocks** | — |
| **估时** | 0.5 d |
| **Owner** | __ |
| **PR 标题** | `refactor(runtime): scheduler worker routes scheduled wakes through DispatchAssembler` |

## 目标

把定时唤醒（`wake_at <= now`）也迁到 Assembler，使主仓内 `dispatch` 只剩 Assembler 一个出口。

## 范围

- `novaic-agent-runtime/task_queue/workers/scheduler_worker_sync.py`
- 相关调度逻辑（若在别处）

## 前置 Checklist

- [ ] PR-10 合并
- [ ] PR-11 / PR-12 顺序无强依赖，可与它们并行

## 实施 Checklist

- [ ] Worker 构造 Assembler 实例，`service_name="runtime-scheduler"`
- [ ] 替换所有 `POST /api/queue/dispatch` 的手工拼装 → `assembler.assemble_and_dispatch(TriggerType.SCHEDULED_WAKE, agent_id, ...)`
- [ ] 若当前 scheduler 传 `trigger_type="system_wake"` 之类的字符串 → 用 `TriggerType.SCHEDULED_WAKE` 或 `SYSTEM_WAKE` 对应
- [ ] `DispatchError` 处理：
  - `no_owner` → log ERROR + 跳过该次唤醒（标记 subagent 状态异常，后续靠 PR-26 alert）
  - `queue_4xx` → log ERROR（通常是合约 bug，不应重试）
  - `queue_5xx / network` → 保留默认重试（scheduler 的 tick 自然会再来）

## 测试 Checklist

- [ ] 单测：mock Assembler → 验证到点被调一次
- [ ] 集成：造一个 `wake_at = now - 1s` 的 subagent → scheduler tick 后 Assembler 调一次 dispatch

## 可观测性 Checklist

- [ ] metric `scheduler_wake_total{result}` counter
- [ ] log：`event=scheduled_wake agent=... due_at=... result=...`

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) P1-8 → `[x]`
- [ ] 本工单 Status → `[x]`
- [ ] PR-03 allowlist 移除 `scheduler_worker_sync.py`

## 验收命令

```bash
rg 'httpx\..*/dispatch' novaic-agent-runtime/
# 预期：仅 queue_service/routes.py（端点定义）
```

## 回滚

`git revert` — 独立。

## 备注

- 合完这一条，M1 达成（上游 dispatch 完全收敛至 Assembler）。
- 下一步进入 Phase 2（主路径切换）。
