# PR-165C — Notification Lifecycle Close / Failure Semantics

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-agent-runtime`, `novaic-business`, docs |
| Depends on | PR-165B |
| Theme | Lifecycle ownership |

## Goal

Confirm and tighten notification lifecycle ownership after prompt cutover:
`session_init` claims wake notifications, successful wake close marks them
processed/consumed, and failure paths leave enough state for recovery without
pretending a message was observed or handled.

## Plan

1. Audit `session_init`, pending-trigger buffering, `scope_end`, health
   recovery, and Business Environment transition code.
2. Add tests for success, archive failure, and missing/invalid notification id
   semantics.
3. Remove or guard any remaining path that treats read/unread UI status as
   agent-loop state.
4. Smoke a normal wake close and a forced failure/recovery shape where feasible.
5. Deploy, verify, and commit.

## Current-State Analysis

- Runtime `session_init` appends the current wake's `message_ids` into Cortex
  `scope.meta.input_message_ids` and transitions those ids to `claimed`.
- Runtime `cortex.scope_end` snapshots `input_message_ids` before archive,
  then transitions them to `consumed` only after `bridge.scope_end(...)`
  succeeds.
- Archive failure raises and skips the consumed transition, so recovery can
  still reason from the `claimed` state.
- Business transition failures during `scope_end` remain soft failures: archive
  success is the authoritative close operation, while the lifecycle transition
  is trace/recovery bookkeeping.
- The remaining entropy was a stale `filter_sending` parameter name in Runtime
  `context.read`, which suggested an old UI receipt/sending filter branch even
  though the code now only appends Environment notifications.

## Required Tests

- Runtime lifecycle test: successful wake close transitions current
  notification ids to processed/consumed.
- Runtime/business test: failed close does not mark notifications processed.
- Guardrail test: agent loop does not consult UI read/unread status.

## Done Criteria

- Notification lifecycle has one owner chain: Subscriber/Queue -> Runtime
  session -> Environment/Business transitions.
- UI message status remains delivery/read presentation only.
- Tests, smoke, deploy, and git commit evidence are recorded here.

## Implementation Notes

- Removed `filter_sending` from Runtime `context.read` and from the
  `cortex.prepare_llm_context` caller.
- Added PR-165C guardrails:
  - `context.read` source must not contain raw Business message fetches.
  - `context.read` source must not contain UI receipt/read-unread markers.
  - lifecycle ownership must remain `session_init -> claimed` and
    `scope_end -> consumed`, with meta read before archive and consume after
    archive.
- Existing lifecycle behavior tests already covered successful consume,
  archive failure, Business soft failure, and missing Business client.

## Validation

- Runtime focused tests:
  `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr165c_notification_lifecycle_guardrails.py tests/test_context_read_by_ids.py tests/test_context_read_ordering.py tests/test_scope_end_consumed.py tests/test_session_init_message_ids.py tests/test_pr116_no_chat_messages_read.py`
  -> `25 passed`.
- Runtime full suite:
  `PYTHONPATH=.:../novaic-common pytest -q` -> `198 passed`.
- Production deploy:
  `./deploy services` completed; `./deploy status` reported backend ports and
  relay healthy.
- Production smoke:
  - Runtime `handle_context_read` source has no raw message fetch /
    `filter_sending` / old IM-header helpers, and appends an
    `ENVIRONMENT_NOTIFICATION` from wake meta.
  - Runtime `handle_cortex_scope_end` archive failure raises and does not call
    `bulk_transition_messages(..., to="consumed")`.

## Git

- Runtime submodule commit: `dd7b96b test(runtime): guard notification lifecycle ownership`.
