# PR-114 — Remove Runtime `session.check_new_messages` Dead Handler

| Field | Value |
| --- | --- |
| Status | `[✓]` — Runtime deployed + remote old-handler deletion verified 2026-04-30 |
| Owner | Codex |
| Created | 2026-04-30 |
| Repos | `novaic-agent-runtime`, parent docs |
| Depends on | PR-46, P6-12, PR-113 |

## 旧分支

Runtime still registers `session.check_new_messages`, but the handler itself says it is no longer called. It reads `messages read=0`, which is exactly the old branch P6-12 retired from runtime semantics.

## Detailed Plan

1. [x] Confirm no internal callers beyond topic registration and contract tests.
2. [x] Delete `TaskTopics.SESSION_CHECK_NEW_MESSAGES`.
3. [x] Delete `handle_session_check_new_messages`.
4. [x] Update runtime contract tests so the removed topic is no longer expected.
5. [x] Add/adjust guardrail asserting Runtime hot code no longer exposes `session.check_new_messages` or `handle_session_check_new_messages`.

## Tests

- [x] `python -m pytest tests/test_runtime_tool_path_contract.py tests/test_pr113_no_wake_im_replay.py`
- [x] `python -m pytest` — 184 passed
- [x] `python -m compileall -q task_queue`

## Smoke / Deploy

- [x] Local `rg "session.check_new_messages|handle_session_check_new_messages|SESSION_CHECK_NEW_MESSAGES" task_queue tests` — only guardrail assertions remain.
- [x] `./deploy runtime`
- [x] `./deploy status`
- [x] Remote `rg` confirms old handler/topic absent from `/opt/novaic/services/novaic-agent-runtime/task_queue`.

## Git

- [x] Runtime commit: `0cf7076 refactor(runtime): remove dead check_new_messages handler (PR-114)`
- [x] Runtime push.
- [x] Parent commit: `df1ab18 docs: create cleanup tickets and close PR-114`
- [x] Parent push.
