# Phase 3B2 Skill Begin End Stack Writes Result

## Summary

Implemented SQLite active-stack projection writes for scope creation, skill_begin, and skill_end. Successful root/wake creation now initializes or updates the active stack projection, successful child skill_begin writes the new top-first stack, and successful child skill_end writes the post-pop stack. Failure branches continue returning existing file-walk stack context without mutating the SQLite projection.

## Done

- Wired `novaic-cortex/novaic_cortex/api.py` to `write_active_stack_projection`.
- Added explicit active stack frame fields from `_collect_active_stack`: `scope_id`, `depth`, `skill_name`, `name`, `kind`, `parent_scope_id`, `scope_path`, and `parent_path`.
- Added projection writes for successful root scope creation, wake creation, child skill_begin, and child skill_end.
- Tightened active stack generation to require the Workspace clock instead of falling back to process time.
- Extended lifecycle tests to assert projection contents after begin/end and assert duplicate/mismatch failures do not mutate projection.
- Updated the test workspace utility to provide an operational SQLite store by default so lifecycle tests exercise the real projection store.

## Verification

- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_context_event_api_skill_lifecycle.py novaic-cortex/tests/test_active_stack_projection.py novaic-cortex/tests/test_operational_store.py`
  - Passed: 15 tests.
- `python3 -m py_compile novaic-cortex/novaic_cortex/api.py novaic-cortex/novaic_cortex/active_stack_projection.py novaic-cortex/tests/workspace_test_utils.py`
  - Passed.
- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_context_event_api_skill_lifecycle.py novaic-cortex/tests/test_active_stack_projection.py novaic-cortex/tests/test_operational_store.py novaic-cortex/tests/test_pr84_minimal_structure_invariants.py novaic-cortex/tests/test_pr234_control_stack.py novaic-cortex/tests/test_pr67_wake_child_api.py novaic-cortex/tests/test_pr56_root_scope_summary.py novaic-cortex/tests/test_pr74_scope_summary_contract.py novaic-cortex/tests/test_context_event_api_steps_write.py novaic-cortex/tests/test_context_event_api_context_writes.py novaic-cortex/tests/test_context_event_write_authority.py`
  - Passed: 42 tests.
- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests`
  - Passed: 438 tests.
- Static search confirmed active-stack projection write/read call sites are explicit and `time.time()` is not used in this active-stack control chain.

## Known Gaps

- Runtime reads still use the existing file-walk `_collect_active_stack`; P019/P020 are responsible for cutting reads and routing authority over to SQLite and quarantining file-walk authority.
- Runtime projection writes currently update the active-stack projection only; audit event append remains available in the helper but is not used on begin/end to avoid idempotency conflicts before the finalize event design lands.

## Artifacts

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_context_event_api_skill_lifecycle.py`
- `novaic-cortex/tests/workspace_test_utils.py`
