# P531 Check: Run Static Residue Scan

## Summary

Success. P531 ran the static residue scan and saved raw output plus mechanical production/test grouping.

## Evidence

- Result: `R524`
- Command artifact: `.complex-problems/L20260516-222011/tmp/p531/static-residue-scan-command.txt`
- Raw hits: `.complex-problems/L20260516-222011/tmp/p531/static-residue-raw.txt`
- Production hits: `.complex-problems/L20260516-222011/tmp/p531/static-residue-production.txt`
- Test hits: `.complex-problems/L20260516-222011/tmp/p531/static-residue-tests.txt`
- Counts:
  - Raw hits: 395
  - Production hits: 150
  - Test hits: 245
  - Production files: 27
  - Test files: 56

## Criteria Map

- Exact pattern and command recorded: satisfied.
- Raw scan output saved: satisfied.
- Production and test split files saved: satisfied.
- Total/production/test counts recorded: satisfied.
- No classification attempted beyond mechanical path grouping: satisfied.

## Execution Map

- Loaded P514 guard pattern.
- Ran scan over P514 scope.
- Split hits by path prefix into production and tests.
- Saved counts and file lists.

## Stress Test

- No-hit false success risk: rejected by nonzero raw hit count.
- Missing classification risk: intentionally deferred to P532.
- Scope risk: command artifact records the exact scanned paths.

## Residual Risk

The production hit set is large enough that P532 must classify carefully. P531 alone does not prove no risky residue remains.

## Result IDs

- `R524`
