# 2-4-hit low-density tests classified

## Summary

Classified the 2-4-hit low-density test bucket: 43 hits across 17 files. All hits are expected boundary, integration, source-guard, or regression coverage. No stale or misleading test residue was found.

## Done

- Filtered P531 test hits to the P545-owned 17 files.
- Counted 43 hits across 17 files.
- Wrote a classification table with one rationale per file.

## Verification

- `two-to-four-hit-test-counts.txt` reports 43 hits / 17 unique files.
- The classification table contains exactly 17 file rows.
- Hit-line review confirmed legacy words occur in negative guards or retired-path regression tests, while `publish`, `active`, and `remaining_stack` hits cover current queue/session boundaries.

## Known Gaps

- None for this bucket.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p545/file-list.txt`
- `.complex-problems/L20260516-222011/tmp/p545/two-to-four-hit-test-hits.txt`
- `.complex-problems/L20260516-222011/tmp/p545/two-to-four-hit-test-counts.txt`
- `.complex-problems/L20260516-222011/tmp/p545/two-to-four-hit-test-lines.txt`
- `.complex-problems/L20260516-222011/tmp/p545/two-to-four-hit-test-classification.md`
