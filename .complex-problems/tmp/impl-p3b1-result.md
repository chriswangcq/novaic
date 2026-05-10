# P022 T017 Result - Active Stack Projection Helper

## Summary

Added a focused active-stack projection helper and tests. The helper normalizes top-first frames, writes `active_stack_projection`, and optionally records an idempotent durable stack projection event in `scope_events`.

## Done

- Added `novaic_cortex.active_stack_projection`.
- Implemented `normalize_active_stack_frames(frames)`.
- Implemented `write_active_stack_projection(operational_store, root_scope_id, frames, generation, reason, idempotency_key=None)`.
- Added stable frame filtering for `scope_id`, `depth`, `skill_name`, `name`, `task`, `kind`, `parent_scope_id`, `scope_path`, and `parent_path`.
- Added explicit input validation for store, root scope id, generation, reason, frame type, and `scope_id`.
- Added tests for deterministic normalization, malformed inputs, empty stack writes, nested top-first stack writes, idempotent event retry, and required explicit inputs.

## Verification

- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_active_stack_projection.py novaic-cortex/tests/test_operational_store.py` passed: 11 tests.
- `python3 -m py_compile novaic-cortex/novaic_cortex/active_stack_projection.py novaic-cortex/novaic_cortex/operational_store.py` passed.

## Known Gaps

- Runtime `skill_begin`, `skill_end`, and finalize are not wired yet; that remains P023/P024.
- Projection upsert and event append are separate store calls in this helper. A later hardening pass may add a compound store method if strict single-transaction stack event plus projection is required.

## Artifacts

- `novaic-cortex/novaic_cortex/active_stack_projection.py`
- `novaic-cortex/tests/test_active_stack_projection.py`
