# Cortex Boundary Call Path Map Check

## Summary

P559 is successful. R549 maps Cortex-side boundary direction with scan artifacts and flags `Workspace.materialize()` for later residue classification instead of prematurely deleting or approving it.

## Evidence

- R549.
- `.complex-problems/L20260516-222011/tmp/p559/cortex-boundary-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p559/cortex-boundary-counts.md`
- `.complex-problems/L20260516-222011/tmp/p559/cortex-boundary-slices.txt`
- Source slices from `sandbox.py`, `logical_fs.py`, `shell_capabilities.py`, `blob_payload.py`, and `workspace.py`.

## Criteria Map

- Scans Cortex imports/calls for relevant terms: satisfied by boundary scan artifact.
- Reads high-signal Cortex files: satisfied by source slices and R549.
- Classifies current call direction and suspicious direct paths: satisfied by R549.
- Records exact commands and artifacts: satisfied by artifacts.

## Execution Map

- Ran broad Cortex boundary scan.
- Read bounded high-signal source files.
- Identified intended shell/LogicalFS/blob direction.
- Flagged `Workspace.materialize()` for P553 classification.

## Stress Test

- One-go skepticism: the result makes no code change and does not close the flagged materialize surface.
- False positive stress: blob payload and runtime-artifact usage are classified as intended artifact storage, not real-time RO/RW authority.
- False negative stress: scan included broad vocabulary and source slices, but dynamic env/service URLs remain a known limitation for P557/P553.

## Residual Risk

Cortex-only map cannot prove sandbox/logicalfs internals; P560 covers that. `Workspace.materialize()` remains an explicit item for P553.

## Result IDs

- R549
