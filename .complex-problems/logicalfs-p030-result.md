# Result: Direct Cortex Constructor Tests Migrated

## Summary

P030 migrated direct runtime test construction away from `Cortex(store, agent_id=...)` and into the explicit Workspace/LogicalFS authority boundary.

## Done

- Added `make_cortex_with_store(...)` to `tests/workspace_test_utils.py`.
- Replaced all live test usages of direct Cortex store constructors in:
  - `tests/test_archive_invariants.py`
  - `tests/test_compaction_meta.py`
  - `tests/test_context_budget_limits.py`
  - `tests/test_cortex_chaos.py`
  - `tests/test_engine_wiring.py`
  - `tests/test_hooks_limits.py`
  - `tests/test_hooks_metrics.py`
  - `tests/test_runtime.py`
  - `tests/test_runtime_path_abuse.py`
  - `tests/test_skill_install_limits.py`
  - `tests/test_skill_lifecycle.py`
  - `tests/test_suggest_compact.py`
  - `tests/test_tool_metrics.py`
  - `tests/test_wave4_metrics.py`
- Preserved store pre-seeding and inspection by passing existing `MemoryStore` instances into the helper where needed.
- Preserved hook injection by passing hooks into both Workspace and Cortex through the helper.

## Evidence

- P030 targeted runtime/tool/hook/engine tests passed:

```text
77 passed in 0.21s
```

- Broader P028 migrated test set still passed after helper changes:

```text
111 passed in 0.39s
```

- Direct constructor residue scan:

```text
rg -n "\bCortex\((MemoryStore\(\)|store|[^\n]*agent_id=|[^\n]*, agent_id)" tests -g '*.py'
# no matches
```

- Broad `Cortex(` scan:

```text
tests/workspace_test_utils.py:38:        Cortex(
```

## Residuals

- No direct Cortex constructor residue remains in tests. Full cutover and old implementation residue scans remain under P031/P024.
