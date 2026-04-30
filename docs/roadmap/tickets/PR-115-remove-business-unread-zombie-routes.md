# PR-115 — Remove Business `messages/unread*` Zombie Routes

| Field | Value |
| --- | --- |
| Status | `[✓]` |
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

1. [x] Confirm callers are absent in active repos.
2. [x] Delete the four routes from `business/internal/message.py`.
3. [x] Remove now-unused helper code if only used by those routes.
4. [x] Add/adjust guardrail proving unread zombie routes do not exist.
5. [x] Keep canonical message creation/listing paths intact.

## Tests

- [x] `python -m pytest tests/test_pr115_unread_routes_removed.py tests/test_schema_invariants.py tests/test_message_trace.py tests/test_orphaned_endpoint.py tests/test_bulk_transition.py`
- [x] `python -m pytest`
- [x] `python -m compileall -q business`

## Smoke / Deploy

- [x] Local `rg "messages/unread|unread-count|unread-sent|unread-grouped" business` has no hits.
- [x] `./deploy business`
- [x] `./deploy status`
- [x] Remote `rg` confirms zombie routes absent from `/opt/novaic/services/novaic-business/business`.

## Git

- [x] Business commit: `refactor(business): remove unread zombie routes (PR-115)`
- [x] Business push.
- [ ] Parent commit: `docs: close business unread route cleanup (PR-115)`
- [ ] Parent push.
