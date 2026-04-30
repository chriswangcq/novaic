# PR-115 — Remove Business `messages/unread*` Zombie Routes

| Field | Value |
| --- | --- |
| Status | `[ ]` |
| Owner | Codex |
| Created | 2026-04-30 |
| Repos | `novaic-business`, parent docs |
| Depends on | P6-12, PR-114 |

## 旧分支

Business still exposes deprecated unread routes backed by `chat_messages.read=0`:

- `GET /messages/unread/{agent_id}`
- `GET /messages/unread-sent/{agent_id}`
- `GET /messages/unread-count/{agent_id}`
- `GET /messages/unread-grouped`

They are documented as zombie/no internal callers. Keeping them encourages callers to revive `read=0` as a runtime input source.

## Detailed Plan

1. Confirm callers are absent in active repos.
2. Delete the four routes from `business/internal/message.py`.
3. Remove now-unused helper code if only used by those routes.
4. Add/adjust guardrail proving unread zombie routes do not exist.
5. Keep canonical message creation/listing paths intact.

## Tests

- [ ] `python -m pytest tests/test_schema_invariants.py tests/test_message_actions.py`
- [ ] `python -m pytest`
- [ ] `python -m compileall -q business`

## Smoke / Deploy

- [ ] Local `rg "messages/unread|unread-count|unread-sent|unread-grouped" business tests`.
- [ ] `./deploy business`
- [ ] `./deploy status`
- [ ] Remote `rg` confirms zombie routes absent from `/opt/novaic/services/novaic-business/business`.

## Git

- [ ] Business commit: `refactor(business): remove unread zombie routes (PR-115)`
- [ ] Business push.
- [ ] Parent commit: `docs: close business unread route cleanup (PR-115)`
- [ ] Parent push.

