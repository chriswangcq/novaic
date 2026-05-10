# Result: Remaining Workspace Constructor Tests Migrated

## Summary

P029 migrated the remaining direct Workspace constructor tests in the selected Cortex test set to the LogicalFS authority helper boundary.

## Done

- Updated `tests/workspace_test_utils.py` with a shared `make_cortex_with_store(...)` helper built on `make_workspace_with_store(...)`, so runtime facade tests can use the same LogicalFS authority boundary as Workspace tests.
- Updated direct old-constructor usages in:
  - `tests/test_paths_adversarial.py`
  - `tests/test_step_index_outcome.py`
  - `tests/test_pr74_scope_summary_contract.py`
- Preserved blob payload policy/client test coverage by injecting those dependencies through `make_workspace_with_store(...)`.

## Evidence

- Targeted test command passed:

```text
111 passed in 0.46s
```

- Workspace constructor residue scan:

```text
rg -n "\bWorkspace\(" tests -g '*.py'
tests/workspace_test_utils.py:19:    return Workspace(authority, agent_id, **workspace_kwargs), store
```

## Residuals

- Direct `Cortex(store, agent_id=...)` constructor usages remain in other tests. This is not closed by P029 because P030 explicitly owns direct Cortex constructor migration.
