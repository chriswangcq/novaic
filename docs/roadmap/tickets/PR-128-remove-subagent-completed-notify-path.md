# PR-128: Remove `subagent_completed` notify-parent path

## 背景

`subagent_completed` / `message.notify_parent` 是旧生命周期通知通路。统一 IM 后，结果汇报由 child 显式 `subagent_send(parent, message)` 完成；completed 只应是内部 lifecycle，不应再触发 parent wake 或拼接消息。

## Scope

- Runtime wake finalize 删除 `message.notify_parent` step。
- 删除 `MESSAGE_NOTIFY_PARENT` handler/topic。
- 删除 `subagent_completed` dispatch 相关 active references。
- 保留 subagent 状态机完成态，不作为通信通路。

## 非目标

- 不删除 `SPAWN_SUBAGENT` / `SUBAGENT_COMPLETED` message enum；后续票统一清。
- 不改变 `skill_end` / wake close 语义。

## 实施计划

- 从 finalize steps 移除 notify-parent。
- 物理删除旧 handler 或让注册表无引用后删除文件。
- 更新 runtime tests：finalize 不再尝试 dispatch `subagent_completed`。

## 单元测试

- Runtime finalize 测试。
- Runtime tool/path guardrail：active topics 不包含 `MESSAGE_NOTIFY_PARENT`。
- 搜索测试确保无 `trigger_type="subagent_completed"` active code。

## 冒烟测试

- child wake 结束后不产生 `subagent_completed` dispatch。
- child 使用 `subagent_send` 时 parent 正常收到 IM。

## 部署 Checklist

- Runtime 测试通过。
- Runtime 部署。
- 线上日志确认无 `message.notify_parent` / `subagent_completed` dispatch。

## GitHub / Merge

- 依赖 PR-126 preferred。
- Commit message: `refactor(runtime): remove subagent completed notify parent path`

## Closure — 2026-05-01

- Status: verified closed and deployed.
- Verification: Runtime tool-path and wake-finalize contract tests passed; child completion is lifecycle state, not a parent notification channel.
- Current architecture: child result substance must be sent explicitly through `subagent_send`.
