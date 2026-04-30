# PR-116 — Remove `chat_messages.read` UI Compatibility Branch

| Field | Value |
| --- | --- |
| Status | `[✓]` |
| Owner | Codex |
| Created | 2026-04-30 |
| Repos | `novaic-agent-runtime`, `novaic-business`, `novaic-app`, parent docs |
| Depends on | P6-12, PR-114, PR-115 |

## 旧分支

`chat_messages.read` was downgraded to UI-only, but active code still writes and reads it for delivery/read-state compatibility. This keeps a confusing field alive next to `lifecycle`.

## Detailed Plan

1. [x] Audit all active reads/writes of message `read`.
   - Runtime: `context.read` consumed messages by `input_message_ids` but still wrote `{"read": 1}`; `chat_reply` still inserted `read=1`.
   - Business: message writers inserted `read=0`; `messages.mark_all_read`, `/chat/clear`, schema field, and App contract kept the old branch alive.
   - App: `useMessages` converted `read` into user-message `Read` status and assistant unread count; `ChatInput` / `MessageList` called `mark_all_read`.
2. [x] Replacement decision:
   - User message status becomes view-local only: optimistic `_opt_` → `sending`, confirmed row → `delivered`.
   - No durable unread/read receipt column. If unread UX returns later, implement it as a front-end viewport/session state, not `chat_messages.read`.
3. [x] Remove App display/action dependencies on `read` and `mark_all_read`.
4. [x] Remove Runtime writes of `{"read": 1}` and `read=1`.
5. [x] Remove Business `read` writes, schema field, `mark_all_read`, and `/chat/clear` read-marking compatibility.
6. [x] Update shared App Entangled contract and generated App types.
7. [x] Add guardrails so `chat_messages.read` and `mark_all_read` do not reappear.

## Tests

- [x] Runtime relevant tests for context read and chat_reply.
- [x] Business message/schema tests.
- [x] App unit/typecheck/build tests for message display.
- [x] Common contract tests if affected.
- [x] Runtime full `python -m pytest`.
- [x] Business full `python -m pytest`.
- [!] App full `npm run test:unit` has an unrelated existing `ExecutionLog.test.tsx` expectation failure; targeted contract test and `npm run build` passed.

## Smoke / Deploy

- [x] Send/receive path covered by Runtime/Business/App contract tests and App build; message status no longer depends on `read`.
- [x] Runtime/Business/App deploys as needed.
- [x] Remote grep confirms Runtime/Business active code has no semantic `chat_messages.read` writes.
- [x] Remote shared contract confirms `messages.actions == ["send", "clear"]` and no `read` field.

## Git

- [x] Runtime/Business/App/Common commits as affected.
- [x] Parent docs/submodule commit.
- [x] Push all changed repos.

## Risk Note

This ticket must not be implemented by blindly deleting the field. The UI contract must be inspected first, then the old branch removed from the bottom up.
