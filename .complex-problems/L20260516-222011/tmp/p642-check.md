# P642 Runtime and Tool RW Fixture Rewrite Check

## Summary

Success. Targeted runtime/tool fixture files no longer use root `/rw/scratch`, and focused tests pass with the same truncation, hooks, metrics, chaos, and read/write behavior covered.

## Evidence

- `.complex-problems/L20260516-222011/tmp/p642-scan.txt`: no `/rw/scratch` remains in targeted files.
- `.complex-problems/L20260516-222011/tmp/p642-tests.txt`: 14 tests passed.
- R630 lists each touched path replacement.

## Criteria Map

- Target files no longer use root `/rw/scratch`: satisfied.
- Preserves runtime/tool behavior: satisfied by focused tests.
- Runs focused tests: satisfied.

## Execution Map

- T636 marked executing.
- Rewrote five test files to use `/rw/tmp`.
- Ran post-change scan and focused tests.
- Recorded R630.

## Stress Test

The preloaded store-key runtime test was updated on both the object key and logical read path, avoiding a split-brain fixture where storage and read path diverge.

## Residual Risk

Path traversal/adversarial root scratch strings are intentionally left to P643.

## Result IDs

- R630
