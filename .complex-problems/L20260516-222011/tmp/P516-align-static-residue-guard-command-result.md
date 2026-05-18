# P516 Align Static Residue Guard Command Result

## Summary

Aligned the static residue guard command with the guard taxonomy and regenerated the preview without path errors.

## Done

- Rewrote the proposed scan command as a readable `PATTERN=...; rg "$PATTERN" ...` command.
- Added missing taxonomy terms to the executable pattern: `active_session`, `SessionDecision`, and `optional`.
- Added pattern artifacts for machine/human review.
- Regenerated the preview artifact using the corrected path set.

## Verification

- Guard design: `.complex-problems/L20260516-222011/tmp/p514/static-residue-guard-design.md`
- Pattern artifact: `.complex-problems/L20260516-222011/tmp/p514/guard-pattern.txt`
- Term list: `.complex-problems/L20260516-222011/tmp/p514/guard-terms.txt`
- Alignment check: `.complex-problems/L20260516-222011/tmp/p514/guard-term-alignment.txt`
- Alignment check reports `0` missing terms.
- Preview artifact: `.complex-problems/L20260516-222011/tmp/p514/static-residue-guard-preview.txt`

## Known Gaps

- None for P516. P512 still owns full scan classification.
