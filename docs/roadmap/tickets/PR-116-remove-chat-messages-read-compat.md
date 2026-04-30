# PR-116 — Remove `chat_messages.read` UI Compatibility Branch

| Field | Value |
| --- | --- |
| Status | `[ ]` |
| Owner | Codex |
| Created | 2026-04-30 |
| Repos | `novaic-agent-runtime`, `novaic-business`, `novaic-app`, parent docs |
| Depends on | P6-12, PR-114, PR-115 |

## 旧分支

`chat_messages.read` was downgraded to UI-only, but active code still writes and reads it for delivery/read-state compatibility. This keeps a confusing field alive next to `lifecycle`.

## Detailed Plan

1. Audit all active reads/writes of message `read`.
2. Decide the replacement UI signal from existing fields before deleting writes:
   - expected direction: derive chat status from `lifecycle` / message ownership / execution events, not `read`.
3. Update App display logic first if it still consumes `read`.
4. Remove Runtime writebacks of `{"read": 1}`.
5. Remove Business message action helpers that expose read/unread semantics.
6. Remove or deprecate schema field only if Entangled/current data contract no longer requires it.
7. Add guardrails so Runtime no longer writes or reads `chat_messages.read`.

## Tests

- [ ] Runtime relevant tests for context read and chat_reply.
- [ ] Business message/schema tests.
- [ ] App unit/typecheck/build tests for message display.
- [ ] Full affected repo tests as feasible.

## Smoke / Deploy

- [ ] Send/receive chat smoke: user message appears, agent reply appears, status does not depend on `read`.
- [ ] Runtime/Business/App deploys as needed.
- [ ] Remote grep confirms Runtime has no semantic `chat_messages.read` writes.

## Git

- [ ] Runtime/Business/App commits as affected.
- [ ] Parent docs/submodule commit.
- [ ] Push all changed repos.

## Risk Note

This ticket must not be implemented by blindly deleting the field. The UI contract must be inspected first, then the old branch removed from the bottom up.

