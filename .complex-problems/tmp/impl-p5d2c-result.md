# Phase 5D.2c execution result

## Summary

Executed the lock/fallback boundary guard ticket. Added a dedicated guard suite for scope-lock fail-closed behavior, Redis startup validation, and removed Cortex compatibility authority paths. Verified the targeted tests and static searches.

## Done

- Added `novaic-cortex/tests/test_lock_and_compat_boundary_guards.py`.
- Guarded that `get_lock_manager()` fails closed when no backend is installed, instead of silently installing or using an in-process fallback.
- Guarded that `install_redis_backend("")` rejects empty Redis URLs and leaves the backend uninstalled.
- Guarded that `install_redis_backend("redis://...")` fails closed when startup Redis ping fails and leaves the backend uninstalled.
- Guarded that Redis ping can only be deferred by explicit `validate_at_startup=False`, and that this still installs the Redis manager rather than a process-local manager.
- Added static guards that `format_for_llm` and `scope_state_log` stay absent from the live `novaic_cortex` package.
- Confirmed existing guards for no legacy DFS context fallback and no SQLite `:memory:` operational-store fallback.

## Verification

- Ran:
  `PYTHONPATH="novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk" pytest -q novaic-cortex/tests/test_lock_and_compat_boundary_guards.py novaic-cortex/tests/test_context_event_no_compat.py novaic-cortex/tests/test_context_event_read_source_guards.py novaic-cortex/tests/test_operational_store.py novaic-cortex/tests/test_sandbox_requires_mount_namespace.py`
- Result: `28 passed in 0.36s`.
- Ran:
  `rg -n "format_for_llm|scope_state_log" novaic-cortex/novaic_cortex -S --glob '!**/__pycache__/**'`
- Result: no matches.
- Ran:
  `python3 -m py_compile novaic-cortex/tests/test_lock_and_compat_boundary_guards.py novaic-cortex/novaic_cortex/scope_locks.py novaic-cortex/novaic_cortex/main_cortex.py`
- Result: passed.
- Cleaned generated `__pycache__` directories under `novaic-cortex` and `novaic-agent-runtime` after tests to avoid stale static-search noise.

## Known Gaps

None for this bounded ticket. Full Cortex suite coverage remains in downstream problem `P064`.

## Artifacts

- `novaic-cortex/tests/test_lock_and_compat_boundary_guards.py`
- `novaic-cortex/tests/test_context_event_no_compat.py`
- `novaic-cortex/tests/test_context_event_read_source_guards.py`
- `novaic-cortex/tests/test_operational_store.py`
- `novaic-cortex/tests/test_sandbox_requires_mount_namespace.py`
