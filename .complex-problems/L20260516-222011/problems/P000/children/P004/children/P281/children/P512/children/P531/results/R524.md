# P531 Run Static Residue Scan Result

## Summary

Ran the P514/P516 static residue guard scan and saved raw output plus mechanical production/test splits.

## Artifacts

- Pattern: `.complex-problems/L20260516-222011/tmp/p514/guard-pattern.txt`
- Command: `.complex-problems/L20260516-222011/tmp/p531/static-residue-scan-command.txt`
- Raw hits: `.complex-problems/L20260516-222011/tmp/p531/static-residue-raw.txt`
- Production hits: `.complex-problems/L20260516-222011/tmp/p531/static-residue-production.txt`
- Test hits: `.complex-problems/L20260516-222011/tmp/p531/static-residue-tests.txt`
- Counts: `.complex-problems/L20260516-222011/tmp/p531/static-residue-counts.txt`
- Production files: `.complex-problems/L20260516-222011/tmp/p531/static-residue-production-files.txt`
- Test files: `.complex-problems/L20260516-222011/tmp/p531/static-residue-test-files.txt`

## Counts

- Raw hits: 395
- Production hits: 150
- Test hits: 245
- Raw files: 83
- Production files: 27
- Test files: 56

## Production Files

The scan found production hits in 27 files, including queue service, session repository/recovery/outbox, task queue handlers, saga, tool output, and worker effects modules.

## Files Changed

- Ledger artifacts under `.complex-problems/L20260516-222011/tmp/p531/`

No production or test source files were changed.

## Next Step

P532 must classify these hits. P531 does not decide whether any hit is risky.
