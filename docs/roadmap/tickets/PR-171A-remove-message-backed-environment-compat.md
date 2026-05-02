# PR-171A — Remove Message-backed Environment Notification Compatibility

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Parent | [PR-171](PR-171-final-old-path-physical-deletion.md) |
| Repos | novaic-business, novaic-agent-runtime, novaic-cortex |
| Theme | Old path deletion |

## Current-State Analysis

Environment notification is the active loop trigger. The remaining risk is not a known live branch, but regression: user messages must not be replayed into prompts directly, and message lifecycle/read-state must not own Agent loop scheduling.

## Plan

- Re-scan Business/Runtime active sources for message-backed prompt replay, message outbox dispatch, and read/unread loop ownership.
- Re-run existing Environment notification, prompt notification-only, and no-chat-message-read tests.
- Update this ticket with exact closure evidence.

## Verification Required

- [x] Runtime guard tests proving no raw chat-message prompt replay.
- [x] Notification lifecycle guard tests.
- [x] No code fallback to message lifecycle/outbox found in active Runtime loop path.
- [x] No service deploy needed for this ticket because it closed by verification scan; service deploy is covered by PR-171C/PR-171D.
- [x] Parent documentation commit records closure.

## Closure Evidence

- `cd novaic-agent-runtime && PYTHONPATH=.:../novaic-common pytest -q tests/test_context_read_by_ids.py tests/test_pr113_no_wake_im_replay.py tests/test_pr116_no_chat_messages_read.py tests/test_pr165c_notification_lifecycle_guardrails.py tests/test_runtime_tool_path_contract.py` → 20 passed.
- `cd novaic-agent-runtime && PYTHONPATH=.:../novaic-common pytest -q` → 173 passed.
