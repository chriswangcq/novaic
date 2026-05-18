# Final RW Scratch Residue Scan Classification Check

## Summary

Success. The one-go scan result is sufficiently evidenced: it recorded fresh repository scans, included line-context for every remaining root scratch hit, and made a precise classification instead of relying only on prior P640 output.

## Evidence

- `.complex-problems/L20260516-222011/tmp/P644-final-rw-scratch-scan.txt` contains the fresh scan output.
- `.complex-problems/L20260516-222011/tmp/P644-classification-context.txt` contains source/test line context for each hit category.
- Cortex root `/rw/scratch` appears only as a negative guard in `test_workspace.py`.
- Current Cortex scratch behavior is explicitly subagent-scoped in `logical_fs.py` and `test_sandboxd_wiring.py`.
- LogicalFS hits are confined to generic path/cwd/authority tests, not Cortex contract code.

## Criteria Map

- Fresh scans recorded: satisfied.
- Every remaining root `/rw/scratch` hit classified: satisfied by R635 classification list.
- Cortex production code has no positive root scratch contract/default reference: satisfied; production code references only subagent-aware `RW_SCRATCH`.
- Suspicious hits become follow-up if found: satisfied; no suspicious hit remains after context inspection.

## Execution Map

- Ran targeted `rg` scans across Cortex and LogicalFS.
- Inspected the relevant line ranges with `nl`/`sed` for classification.
- Recorded both raw scan and line-context artifacts.

## Stress Test

The test was intentionally string-based and broad for this class of residue: it catches both code and test references that could mislead future agents or regress the contract.

## Residual Risk

A future policy could ban root scratch strings even in LogicalFS generic tests, but that is broader than this Cortex contract cleanup and is not a current blocker.

## Result IDs

- R635
