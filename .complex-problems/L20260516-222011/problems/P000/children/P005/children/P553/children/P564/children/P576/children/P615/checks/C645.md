# P615 Success Check

## Summary

P615 is solved. Cortex persistence/read-model evidence and 33 focused tests show shell/tool result history uses bounded previews/refs/metadata while full details remain recoverable from Cortex step/payload storage.

## Evidence

- `.complex-problems/L20260516-222011/tmp/p615-cortex-persistence-evidence.txt` records scans and corrected code/test slices.
- `.complex-problems/L20260516-222011/tmp/p615-cortex-persistence-tests.txt` shows 33 tests passed.

## Criteria Map

- Persistence scan/slices: satisfied.
- Full output outside normal history via payload refs/files and bounded preview: satisfied by context event/read-model evidence and tests.
- Focused tests: satisfied by 33 passed tests.
- Follow-up if durable inline shell media/raw bytes found: none found.

## Execution Map

- Set P615/T609 executing.
- Captured corrected evidence.
- Ran focused Cortex tests.
- Recorded R604.

## Stress Test

Tests cover context event step writes, read-model truncation, step index artifact metadata, and runtime micro output truncation. This targets the failure mode where full tool bytes leak into normal LLM history instead of staying behind refs.

## Residual Risk

Low. Full payload bytes may exist in durable payload storage by design; the boundary under test is normal history projection, which is covered.

## Result IDs

- R604
