# Phase 5D.2a Scope And Active Stack Guard Coverage Result

## Summary

Reviewed and verified guard coverage for scope uniqueness and active stack authority. Existing tests cover SQLite `scope_projection`, active stack projection write/read/finalize, API lifecycle duplicate rejection, LIFO mismatch, and source guards ensuring runtime reads SQLite active stack projections.

## Done

- Searched tests/source/docs for scope and active stack guard coverage.
- Removed generated `__pycache__` directories that were polluting static searches with stale bytecode names.
- Verified removed runtime authority names do not appear in live source/current contract docs for this area.
- Ran targeted scope/stack tests with explicit sibling-package `PYTHONPATH`.

## Verification

- Static removed-symbol guard:
  - `rg -n "register_scope_id|get_scope_id_index|meta\\.scope_ids|_walk_scope_tree" novaic-cortex/novaic_cortex novaic-cortex/tests docs/cortex/builtin-tools-and-skills.md docs/cortex/invariants.md docs/cortex/scope-lifecycle.md docs/cortex/internal-api-schemas.md -S --glob '!**/__pycache__/**'`
  - returned no matches (`removed_scope_symbols_exit=1`).
- Targeted tests:
  - Initial bare command failed during collection because `logicalfs` was not on `PYTHONPATH`; this was an environment setup issue, not a test failure.
  - Re-run command:
    `PYTHONPATH="novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk" pytest -q novaic-cortex/tests/test_operational_store.py novaic-cortex/tests/test_active_stack_projection.py novaic-cortex/tests/test_context_event_read_source_guards.py novaic-cortex/tests/test_context_event_api_skill_lifecycle.py novaic-cortex/tests/test_pr234_control_stack.py`
  - Result: `45 passed`.

## Guard Coverage Map

| Removed/High-Risk Path | Guard Evidence |
| --- | --- |
| `scope_projection` schema and roundtrip | `test_operational_store.py::test_scope_projection_and_active_stack_roundtrip` |
| active stack persistence/reopen | `test_operational_store.py::test_active_stack_projection_survives_store_reopen` |
| active stack write/read/finalize helpers | `test_active_stack_projection.py` |
| `skill_begin` duplicate rejection via SQLite projection | `test_context_event_api_skill_lifecycle.py` asserts second begin reports `already used` and inspects projection rows |
| nested begin/end top-first active stack | `test_context_event_api_skill_lifecycle.py::test_nested_skill_begin_end_updates_sqlite_active_stack_top_first` |
| LIFO mismatch / stack_top response | `test_context_event_api_skill_lifecycle.py` and `test_pr234_control_stack.py` |
| runtime read routing from SQLite projection | `test_context_event_read_source_guards.py` source guards for status, scope end, skill begin/end, and active write routing |
| deleted file-walk/root-meta authority names | static `rg` returned no live/current matches for `register_scope_id`, `get_scope_id_index`, `meta.scope_ids`, `_walk_scope_tree` |

## Known Gaps

- None for P065. The only issue encountered was missing local `PYTHONPATH` for the new sibling `logicalfs` package; the explicit re-run passed.

## Artifacts

- Test command output: `45 passed`.
- Static search output summarized above.
