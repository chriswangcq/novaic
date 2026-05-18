# Result: P433 / T421 archive projection cleanup

## Summary

Audited workspace archive projection/readback paths. Archive projection still exists intentionally for archive/debug/index materialization, while runtime context/status/scope lookup paths are guarded to use event/SQLite projections instead of DFS/tree-walk fallbacks.

## Verification

- Focused test command:
  - `PYTHONPATH=.:../novaic-common:../novaic-logicalfs:../novaic-sandbox-sdk pytest -q tests/test_context_event_read_source_guards.py tests/test_context_event_no_compat.py tests/test_pr67_wake_child_api.py tests/test_scope_state.py tests/test_pr57_list_archived_summaries.py`
- Result: `42 passed in 0.40s`

## Classification

- `workspace.py::_build_archive_scope_index_projection`: live archive/debug projection helper; intentionally not used for runtime context/status decisions.
- `workspace.py::archive_root_scope_projection`: live archive materialization wrapper after archive event append.
- `api.py::_extract_scope_label`: internal reindex label extraction from archived context/summary; management/index use, not LLM context projection.
- `tests/test_context_event_read_source_guards.py`: guards against DFS/tree-walk fallback in status, skill lifecycle, scope lookup, and scope-end archive reads.
- `tests/test_pr57_list_archived_summaries.py`: asserts old archived summary listing helper is deleted.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p433/focused-pytest.with-status.txt`
- `.complex-problems/L20260516-222011/tmp/p433/archive-projection-guard.txt`
- `.complex-problems/L20260516-222011/tmp/p433/api-archive-label-slice.txt`
- `.complex-problems/L20260516-222011/tmp/p433/workspace-list-recursive-scope-filter-slice.txt`

## Conclusion

No P433 source patch was required. Archive projection is isolated to archive/debug/index materialization; runtime context/status paths are covered by no-DFS guards.
