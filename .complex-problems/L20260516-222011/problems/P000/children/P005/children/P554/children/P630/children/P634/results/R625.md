# Workspace Materialize Removal and Test Rewrite Result

## Summary

Removed the stale `Workspace.materialize()` API from `novaic-cortex/novaic_cortex/workspace.py` and deleted `novaic-cortex/tests/test_workspace_materialize.py`, which only protected the old direct `/rw/scratch` materialization contract. Legitimate LogicalFS provider materialization remains untouched.

## Changes

- Removed `Workspace.materialize()` from `novaic-cortex/novaic_cortex/workspace.py`.
- Deleted `novaic-cortex/tests/test_workspace_materialize.py`.

## Post-Change Scan

Recorded in `.complex-problems/L20260516-222011/tmp/p634-post-change-scan.txt`:

- `Workspace.materialize`, `def materialize`, and `.materialize(` no longer appear in `workspace.py` or tests.
- Remaining `.materialize(` hit is `novaic-cortex/novaic_cortex/logical_fs.py:320`, the intended LogicalFS provider materialization.
- `/rw/scratch` still appears in general workspace/runtime tests and initialization; this is intentionally left for P631 legacy RW scratch layout cleanup rather than silently bundled into P634.

## Verification

- Initial focused test run failed at collection due missing `PYTHONPATH` for sibling `logicalfs` and `sandbox_sdk`; recorded in `.complex-problems/L20260516-222011/tmp/p634-focused-tests.txt`.
- Re-run with monorepo sibling paths succeeded: `.complex-problems/L20260516-222011/tmp/p634-focused-tests-rerun.txt` shows 34 passed.

Command:

```bash
PYTHONPATH="$PWD:$PWD/../novaic-logicalfs:$PWD/../novaic-sandbox-sdk" python -m pytest tests/test_workspace.py tests/test_workspace_limits.py tests/test_workspace_paths.py tests/test_workspace_authority.py tests/test_sandboxd_wiring.py tests/test_context_event_api_context_writes.py -q
```

## Known Gaps

- P631 must classify and clean remaining `/rw/scratch` layout usage.
- The working tree already contained unrelated dirty changes in `novaic-cortex`; this result only claims the method removal and test deletion above.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p634-post-change-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p634-focused-tests.txt`
- `.complex-problems/L20260516-222011/tmp/p634-focused-tests-rerun.txt`
