# PR-153B — Centralize Buffered Input Ownership

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-153 |
| Repos | novaic-business, novaic-agent-runtime, docs |

## Goal

Make the scope that actually starts through `session.init` own `input_message_ids` and message lifecycle `claimed` transitions. Subscriber should dispatch triggers and mark outbox delivery only; it should not append buffered inputs to Cortex or claim messages for an already-running scope.

## Why This Matters

The current buffered path lets Subscriber write `/v1/scope/append_input` and mark buffered messages as claimed by the active scope. If that active scope never reads those appended IDs before finalize, scope_end can still consume them. That is a lifecycle ownership bug.

## Implementation Plan

1. [x] Merge buffered trigger `message_ids` in `SessionRepository` instead of overwriting the pending row.
2. [x] Move `claimed` transition for wake inputs to `session.init`, after the wake scope is created and input IDs are appended.
3. [x] Remove Subscriber's Cortex `append_input` dependency and buffered/saga-started `claimed` transition side effects.
4. [x] Keep outbox delivery/idempotency behavior unchanged.

## Unit / Guardrail Tests

- [x] SessionRepository tests prove pending trigger `message_ids` merge without loss.
- [x] Runtime `session.init` tests prove input messages are claimed by the new wake scope.
- [x] Subscriber tests prove buffered dispatch does not call Cortex `append_input` or message transition.
- [x] Existing context/read, scope_end consumed, and aggregation tests pass.

## Smoke / Deploy / Git

- [x] Smoke quick consecutive messages produce one active session plus pending restart without lost message IDs.
- [x] Deploy Business and Runtime/Queue.
- [x] Commit affected repos.
- [ ] Parent repo submodule/docs commit and push.

## Evidence

- `novaic-business`: `python3 -m pytest tests/test_dispatch_subscriber.py tests/test_im_aggregation.py tests/test_pr52_stale_claim_check.py -q` → 62 passed.
- `novaic-agent-runtime`: `python3 -m pytest tests/test_session_init_message_ids.py tests/test_pr153_pending_inbox_metadata.py tests/test_scope_end_consumed.py tests/test_context_read_by_ids.py -q` → 22 passed.
- `novaic-cortex`: `python3 -m pytest tests -q` → 385 passed, 16 skipped.
- Deploy smoke: `./deploy gateway` restarted Entangled, Gateway, Business, Device, Queue, Storage, Cortex and required Subscriber; `./deploy status` shows all backend ports healthy and relay active.

## Result

Subscriber is back to one job: drain message outbox into Queue triggers and mark outbox delivery/failure. Queue keeps buffered message IDs in `tq_pending_triggers.metadata.message_ids`; Runtime `session.init` writes `scope.meta.input_message_ids` and claims the messages for the wake scope that actually starts.
