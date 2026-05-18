# RW Scratch Cleanup Post-Scan Verification Check

## Summary

Success. The result earned the one-go shortcut: it scanned both Cortex and LogicalFS for root scratch and subagent scratch terms, classified every remaining root `/rw/scratch` occurrence, and backed the classification with focused Cortex and LogicalFS test runs.

## Evidence

- `.complex-problems/L20260516-222011/tmp/p640-postscan.txt` shows the full scan result. Cortex has only one root `rw/scratch` hit, a negative assertion that `rw/scratch/.keep` is absent.
- `novaic-cortex/novaic_cortex/logical_fs.py` still exposes the current intended subagent-aware contract through `/rw/subagents/{subagent_id}/` and `RW_SCRATCH=/cortex/rw/subagents/{subagent_id}/scratch`.
- LogicalFS root `/rw/scratch` hits are confined to lower-layer tests for generic layout/path semantics and do not define Cortex default scratch behavior.
- `.complex-problems/L20260516-222011/tmp/p640-cortex-tests.txt` shows 88 Cortex focused tests passed.
- `.complex-problems/L20260516-222011/tmp/p640-logicalfs-tests-rerun.txt` shows 9 LogicalFS focused tests passed after adding the required `novaic-common` path.

## Criteria Map

- Runs post-change scans for `/rw/scratch`, `RW_SCRATCH`, and `/rw/subagents`: satisfied by `p640-postscan.txt`.
- Classifies remaining root `/rw/scratch` hits: satisfied; Cortex hit is a negative guard, LogicalFS hits are lower-layer generic tests.
- Runs focused Cortex/LogicalFS tests: satisfied by the recorded 88-pass Cortex suite and 9-pass LogicalFS rerun.

## Execution Map

- Scanned `novaic-cortex` and `novaic-logicalfs` for root scratch and subagent scratch terms.
- Confirmed Cortex shell scratch is now subagent-scoped.
- Re-ran the affected Cortex workspace/path/runtime/sandbox wiring tests.
- Re-ran LogicalFS layout/authority tests with corrected dependency path.

## Stress Test

The scan covers the plausible regression mode: stale root `/rw/scratch` references remaining after fixture rewrites. The focused suites cover the places most likely to break from removing the default layout entry and rewriting path fixtures.

## Residual Risk

Lower-layer LogicalFS tests still use `/rw/scratch` as an arbitrary example path. That is not a Cortex contract leak. If the project later wants a repository-wide string-ban, it should be a separate LogicalFS test-contract cleanup, not a blocker for this problem.

## Result IDs

- R633
