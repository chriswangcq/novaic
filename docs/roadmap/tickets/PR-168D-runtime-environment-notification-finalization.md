# PR-168D — Runtime Environment Notification Finalization

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-168 |
| Repos | `novaic-agent-runtime`, docs |
| Depends on | PR-168C |

## Goal

Move Runtime wake claim/finalize ownership from the historical message lifecycle API to the dedicated Environment notification API.

## Current-State Analysis

After PR-168C, the subscriber dispatch loop already claims dedicated Environment notifications for delivery. Runtime still used `bulk_transition_messages(...)` in two hot-path places:

- `session.init` marked current wake ids as `claimed`.
- `scope_end` marked current wake ids as `consumed` after Cortex archive.

That left the semantic loop split across Environment dispatch leases and old chat-message lifecycle state.

## Implementation Checklist

- [x] Add `BusinessClient.transition_environment_notifications(...)` for `/internal/environment/{agent_id}/notifications/{id}/claim|processed|failed`.
- [x] Change `session.init` to mark wake notification ids as `claimed`.
- [x] Change `scope_end` to mark wake notification ids as `processed` only after successful Cortex archive.
- [x] Keep archive failure semantics retryable: no processed transition if scope archival fails.
- [x] Rename/update Runtime tests so they no longer describe `consumed` as the active finalize path.
- [x] Add client contract coverage for Environment notification transition paths.
- [x] Run Runtime unit tests, deploy, and smoke-check deployed source.

## Verification

- `cd novaic-agent-runtime && PYTHONPATH=.:../novaic-common pytest -q tests/test_client_contract.py tests/test_session_init_message_ids.py tests/test_scope_end_environment_notifications.py tests/test_pr165c_notification_lifecycle_guardrails.py` → passed.
- `cd novaic-agent-runtime && PYTHONPATH=.:../novaic-common pytest -q` → 201 passed.
- `./deploy runtime` → deployed Runtime and restarted backend services.
- `./deploy status` → backend ports healthy and relay active.
- Production source smoke on `/opt/novaic/services/novaic-agent-runtime` verified `session.init` and `scope_end` use `transition_environment_notifications(...)` and do not call `bulk_transition_messages(...)`.
- Production Python handler smoke verified `session.init` transitions wake notification ids to `claimed` and `scope_end` transitions them to `processed`.

## Completion Notes

Runtime hot path now treats `scope.meta.input_message_ids` as Environment notification ids. The remaining PR-168 work is physical cleanup: HealthWorker and old `bulk_transition_messages` compatibility still exist outside this hot path and are tracked by PR-168E.
