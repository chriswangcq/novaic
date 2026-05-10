# Migrate miscellaneous runtime lifecycle tests

## Problem

Miscellaneous tests still use runtime lifecycle helpers for setup or convenience. They must be moved to API/projection setup or rewritten so the runtime bypass is not preserved.

## Success Criteria

- `tests/test_engine_wiring.py`, `tests/test_compaction_meta.py`, and `tests/test_cortex_chaos.py` no longer call `cortex.scope_create(...)` or `cortex.scope_end(...)`.
- Each migrated test still asserts its original non-obsolete behavior.
- Focused miscellaneous migrated tests pass.
