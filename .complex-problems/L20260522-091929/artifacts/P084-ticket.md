# Add Task Queue Postgres Claim Recovery And JSONB Query Dialect

## Problem Definition

Task candidate selection in `queue_service/queue_db.py` still embeds SQLite-specific SQL for retry eligibility, dependency readiness, stale recovery, and cancel-by-agent filtering. The Postgres path needs explicit query helpers that generate native `timestamptz` comparisons, JSONB dependency predicates, JSONB agent filters, and row-lock candidate selection before later tickets wire full task mutation semantics.

## Proposed Solution

Add small task query dialect helpers in or near `queue_service/queue_db.py` that generate backend-specific SQL fragments/statements for task claim candidate selection, stale recovery candidate selection, and cancel-by-agent filtering. Keep sqlite SQL unchanged for existing fixtures. Add focused tests that assert the Postgres SQL contains `FOR UPDATE SKIP LOCKED`, native timestamp comparisons, `jsonb_array_elements_text`, `?` JSONB dependency checks, and `payload ->> 'agent_id'`, while sqlite SQL still contains the current SQLite predicates.

## Acceptance Criteria

- Postgres task claim candidate SQL uses native `ts.next_retry_at <= ?` style comparisons without SQLite `datetime(...)`.
- Postgres dependency readiness SQL uses JSONB functions/operators instead of `json_each`/`json_extract`.
- Postgres claim candidate SQL includes `FOR UPDATE SKIP LOCKED` or explicitly documents an equivalent compare-and-update strategy.
- Postgres stale recovery candidate SQL uses native lease heartbeat comparisons without SQLite `datetime(...)`.
- Postgres cancel-by-agent filtering uses `payload ->> 'agent_id'`.
- Focused unit tests assert both Postgres and sqlite dialect outputs without production access.

## Verification Plan

Run the focused task query dialect tests and selected existing TaskQueue sqlite tests such as `tests/test_pr316_taskqueue_state_candidate_cutover.py` and `tests/test_queue_explicit_dependencies.py`.

## Risks

- This ticket may only introduce query helpers and tests; later wiring must still use them in task mutation paths.
- `?` appears both as a JSONB operator and qmark placeholder; tests should ensure the intended SQL text is preserved before adapter conversion.
- Claim semantics still need real mutation/locking tests in P085.

## Assumptions

- P073/P078 adapter conversion preserves JSONB `?` operators.
- P085 will wire task mutation paths to these helpers and verify compare/update behavior.
- Existing sqlite behavior should remain unchanged.
