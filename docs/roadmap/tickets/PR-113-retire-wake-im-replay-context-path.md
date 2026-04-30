# PR-113 — Retire Wake IM Replay Context Path

| Field | Value |
| --- | --- |
| Status | `[✓]` — Runtime deployed + remote old-path deletion verified 2026-04-30 |
| Owner | Codex |
| Created | 2026-04-30 |
| Repos | `novaic-agent-runtime`, parent docs |
| Depends on | PR-67, PR-68, PR-69, PR-70 |

## 背景

Cortex 最小结构已经收敛为两件事：

1. 维护 LIFO scope tree。
2. 由 agent-root scope tree 拼装 LLM context，关闭 scope 时只读取该 scope 的 `summary.md`。

Runtime 里仍残留一条旧的跨 wake 上下文路径：

- `session.init` 写 `wake_replay_pending=True`。
- `context.read` 首轮消费该 flag。
- Runtime 回查已读 `USER_MESSAGE` / `AGENT_REPLY`。
- 拼成 `WAKE_IM_REPLAY` / `<CHAT_HISTORY>` system messages 注入 LLM context。

这条路径会让“消息投递可靠性”和“认知连续性”混在一起，也会形成第二条事实回忆通路。当前目标是拒绝 fallback、物理删除旧路径，只保留 agent-root scope tree。

## 范围

- 删除 Runtime `wake_replay_pending` 写入。
- 删除 Runtime `WAKE_IM_REPLAY` / `<CHAT_HISTORY>` 构造与注入。
- 删除相关 env kill switch / budget helpers / render metrics。
- 删除旧 replay 专项测试。
- 增加 guardrail，确保活代码不再出现旧 replay 标记。
- 保留当前 wake 输入路径：`scope.meta.input_message_ids` → by-id fetch → IM header 渲染。

## 非目标

- 不改 Business system prompt。
- 不改 Cortex DFS 组装。
- 不清历史 ticket 中对 PR-44/PR-50 的事故记录。
- 不引入新的消息 replay/fallback。

## 实施清单

- [x] Runtime: 移除 `task_queue/handlers/runtime_handlers.py` 中 `WAKE_IM_REPLAY_ENABLED_TRIGGERS` 和 `wake_replay_pending` 写入。
- [x] Runtime: 移除 `task_queue/handlers/context_handlers.py` 中 replay helpers、`WAKE_IM_REPLAY` 注入、相关 metrics。
- [x] Runtime: 删除旧 replay 测试 `test_wake_im_replay.py`、`test_pr50_chat_history_byte_cap.py`、`test_wake_im_render_metric.py`。
- [x] Runtime: 新增 guardrail 单测，禁止 `task_queue` 活代码出现 `WAKE_IM_REPLAY`、`<CHAT_HISTORY>`、`wake_replay_pending` 等旧标记。
- [x] Docs: 更新优化建议，说明旧 IM replay path 已由 PR-113 关闭。

## 单元测试

- [x] `python -m pytest tests/test_pr113_no_wake_im_replay.py`
- [x] `python -m pytest tests/test_im_rendering.py tests/test_session_init_message_ids.py tests/test_pr65_agent_root_scope.py tests/test_pr67_wake_child_scope.py tests/test_pr85_llm_context_smoke_guardrails.py tests/test_llm_prompt_contract.py`
- [x] `python -m pytest` — 183 passed
- [x] `python -m compileall -q task_queue`

## 冒烟测试

- [x] `rg` 本地确认 `novaic-agent-runtime/task_queue` 不含旧 replay 标记。
- [x] 部署后远端确认 `/opt/novaic/services/novaic-agent-runtime/task_queue` 不含旧 replay 标记。
- [x] Runtime deploy status 正常。

## 部署

- [x] `./deploy runtime`
- [x] `./deploy status`

## GitHub / 提交

- [ ] Runtime repo commit: `refactor(runtime): remove wake IM replay context path (PR-113)`
- [ ] Runtime repo push。
- [ ] Parent repo commit: `docs: close wake IM replay cleanup (PR-113)`
- [ ] Parent repo push。

## 验收

- LLM context 里跨 wake 信息只来自 agent-root scope tree。
- 当前 wake 输入仍来自 `input_message_ids` by-id assembly。
- Runtime 不再通过已读 chat history 修补 continuity。
- 没有旧 replay kill switch 或 fallback 分支残留。
