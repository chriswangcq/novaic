# Final RW Scratch Residue Scan Result

## Summary

Completed the final residue scan/classification. Cortex does not contain a positive production or fixture contract for root `/rw/scratch`; the only Cortex root scratch occurrence is a negative guard asserting the old default `.keep` is absent. The active scratch contract remains subagent-aware through `/rw/subagents/{id}/scratch` and `RW_SCRATCH`.

## Recorded Scans

- `.complex-problems/L20260516-222011/tmp/P644-final-rw-scratch-scan.txt` records the fresh `rg` scans across `novaic-cortex` and `novaic-logicalfs`.
- `.complex-problems/L20260516-222011/tmp/P644-classification-context.txt` records selected line-context for classification.

## Classification

- `novaic-cortex/tests/test_workspace.py:21`: negative guard; asserts `rw/scratch/.keep` is not created by `Workspace.initialize()`.
- `novaic-cortex/novaic_cortex/logical_fs.py:214,266`: intended current contract; mounts `/rw/subagents/{subagent_id}/` and sets `RW_SCRATCH` to `/cortex/rw/subagents/{subagent_id}/scratch`.
- `novaic-cortex/tests/test_sandboxd_wiring.py:141-142`: intended current contract test; verifies current subagent scratch is mounted and another subagent's scratch is excluded.
- `novaic-logicalfs/tests/test_logicalfs.py:42`: lower-layer generic materialization/cwd test; `cwd="scratch"` intentionally maps to `/cortex/rw/scratch` as an arbitrary relative working directory, not as Cortex default scratch.
- `novaic-logicalfs/tests/test_authority.py:72,79-87,112,119`: lower-layer generic path and initialize-layout tests; they verify LogicalFS can map/read/write/delete/init arbitrary `/rw` paths and do not define Cortex default layout.

## Follow-Up Decision

No follow-up required. There is no Cortex positive root `/rw/scratch` default/canonical reference. Remaining LogicalFS root scratch strings are generic lower-layer examples and should only be changed if a separate repository-wide string-ban is desired.
