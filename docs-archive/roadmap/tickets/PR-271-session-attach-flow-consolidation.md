# PR-271 — Session Attach Flow Consolidation

Status: Closed

## Goal

Consolidate the duplicated active-attach and race-lost-attach branches in `SessionRepository.dispatch()`.

## Why

Both branches perform the same workflow: build attach effect, record a transition, publish outbox, and mark the input event consumed. Duplicating this code creates a misleading second path that can drift during future FSM changes.

## Scope

- Extract a single helper for attach request publication and consumption.
- Keep caller-specific event names and consume reasons explicit.
- Preserve existing dispatch results and delivery behavior.
- Add a source guard that `build_attach_input_effect()` has one live owner inside `SessionRepository`.

## Non-Goals

- Do not change attach semantics.
- Do not alter outbox dispatcher behavior.
- Do not change the pure dispatch FSM.

## Acceptance Criteria

- `SessionRepository.dispatch()` uses one helper for both attach paths.
- Existing active attach and race attach tests pass.
- Source guard prevents reintroducing duplicated attach effect construction in `SessionRepository`.
- Full `novaic-agent-runtime` test suite passes.

## Verification

- `pytest tests/test_pr271_session_attach_flow_consolidation.py tests/test_pr233_active_inbox_dispatch.py tests/test_pr238_generation_checked_attach.py tests/test_pr248_attach_outbox_cutover.py tests/test_pr240_input_consumption.py`
- `pytest`
- `git diff --check`

## Closure Notes

- Added `_publish_attach_request_after_transaction()` as the single owner for attach effect construction, transition recording, outbox publishing, and input consumption.
- Replaced normal active attach and race-lost attach duplicate blocks with calls to the helper.
- Added PR-271 source guard proving one `build_attach_input_effect()` owner remains in `SessionRepository`.
- Verified targeted suite: 19 passed.
- Verified full runtime suite: 311 passed.
- Verified `git diff --check`: clean.
