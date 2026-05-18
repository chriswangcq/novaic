# Wake finalize mutation payload propagation

## Problem Definition

Downstream handlers can only enforce stale-finalize guards if `wake_finalize` propagates the required identity fields into every mutating task payload. Cortex scope-end, session-ended, and terminal subagent status payloads must all carry explicit wake/session identity and reject missing/non-positive generation at build time.

## Proposed Solution

1. Inspect every payload builder in `task_queue/sagas/wake_finalize.py`:
   - `_build_cortex_scope_end_payload`
   - `_build_session_ended_payload`
   - `_build_set_sleeping_payload`
   - `_build_set_subagent_completed_payload`
2. Add or update tests so a single representative finalize context proves all mutating payloads carry required identity:
   - `scope_id`
   - positive `session_generation` / `generation` as required by the receiving handler.
   - root/wake scope metadata for Cortex/session payloads where available.
3. Verify all builders reject missing and zero generation rather than defaulting.
4. Run source guards for generation defaulting and missing identity in `wake_finalize.py`.

## Acceptance Criteria

- All wake-finalize mutating payload builders include the identity required by their downstream handlers.
- Missing or zero generation is rejected by every finalize mutation payload builder.
- Tests cover Cortex scope-end, session-ended, sleeping, and completed payloads together.
- Source guard shows no default-to-zero generation behavior in `wake_finalize.py`.

## Verification Plan

- `python3 -m py_compile task_queue/sagas/wake_finalize.py`
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr43_last_scope_wiring.py tests/test_pr254_finalize_ownership.py tests/test_pr311_saga_compensation_outbox_cutover.py tests/test_finalize_summary_boundary.py`
- `rg` guards over `task_queue/sagas/wake_finalize.py` for generation defaulting and missing last-scope residue.

## Risks

- P355 may discover the behavior is already present from P353/P354; in that case it should still add/confirm an aggregate payload test rather than silently rely on dispersed coverage.

## Assumptions

- Handler-side validation and ordering have already been handled by P354 children; P355 is specifically about payload propagation completeness.
