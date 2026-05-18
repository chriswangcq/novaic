# P514 Check Not Successful

## Summary

P514 is not yet successful. The guard design lists `active_session`, `SessionDecision`, and `optional` as guard terms, but the proposed scan command does not include all of them. This creates a mismatch between the taxonomy and executable scan.

## Evidence

- Result: `R506`
- Guard design: `.complex-problems/L20260516-222011/tmp/p514/static-residue-guard-design.md`
- Mismatch: `active_session`, `SessionDecision`, and `optional` appear in guard term prose but not the proposed command.

## Criteria Map

- Guard terms explicit: satisfied.
- Scan command defined: partially satisfied, but incomplete relative to the term list.
- Expected categories listed: satisfied.

## Execution Map

- P514 wrote a guard design and preview.
- Strict review compared prose guard terms against the proposed command and found missing terms.

## Stress Test

- If left unfixed, P512 could report clean residue while silently skipping singular active-session references or optional compatibility language.
- The fix is narrow: align the command exactly with the listed guard terms and rerun preview.

## Residual Risk

Until the command is aligned with the taxonomy, P514 cannot be considered a reliable input to P512.

## Result IDs

- `R506`
