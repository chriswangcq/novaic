# RW Scratch Cleanup Post-Scan Verification Result

## Summary

Completed final RW scratch cleanup guard. Cortex no longer advertises root `/rw/scratch` as a default/canonical scratch path; the only Cortex root scratch hit is a negative assertion that the old default `.keep` is absent. Current shell scratch remains subagent-aware via `RW_SCRATCH=/cortex/rw/subagents/{id}/scratch`.

## Scan Classification

- Cortex current intended contract:
  - `novaic-cortex/novaic_cortex/logical_fs.py` mounts `/rw/subagents/{id}/` and sets `RW_SCRATCH` to `/cortex/rw/subagents/{id}/scratch`.
  - `novaic-cortex/tests/test_sandboxd_wiring.py` verifies current-subagent RW scratch is mounted and other subagent scratch is excluded.
- Cortex remaining root `/rw/scratch` hit:
  - `novaic-cortex/tests/test_workspace.py` is a negative guard asserting `rw/scratch/.keep` is not created by `Workspace.initialize()`.
- LogicalFS remaining root `/rw/scratch` hits:
  - `novaic-logicalfs/tests/test_authority.py` and `tests/test_logicalfs.py` are lower-layer generic path/layout fixtures, not Cortex semantic/default layout. They do not reintroduce root scratch as Cortex contract.

## Verification

- `.complex-problems/L20260516-222011/tmp/p640-postscan.txt` records full scans.
- Cortex focused suite: `.complex-problems/L20260516-222011/tmp/p640-cortex-tests.txt` shows 88 passed.
- First LogicalFS test run missed `novaic-common` on `PYTHONPATH`; recorded in `.complex-problems/L20260516-222011/tmp/p640-logicalfs-tests.txt`.
- Corrected LogicalFS rerun: `.complex-problems/L20260516-222011/tmp/p640-logicalfs-tests-rerun.txt` shows 9 passed.

## Known Gaps

- No Cortex cleanup follow-up required.
- If the desired future policy becomes "no `/rw/scratch` string anywhere, even in lower-layer generic tests," that would be a separate LogicalFS test-contract cleanup, not a current Cortex layering bug.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p640-postscan.txt`
- `.complex-problems/L20260516-222011/tmp/p640-cortex-tests.txt`
- `.complex-problems/L20260516-222011/tmp/p640-logicalfs-tests.txt`
- `.complex-problems/L20260516-222011/tmp/p640-logicalfs-tests-rerun.txt`
