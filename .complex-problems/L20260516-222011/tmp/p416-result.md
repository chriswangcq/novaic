# Cortex residue inventory result

## Summary

P416 completed a Cortex-only residue inventory and live-surface map. The targeted default/fallback guard found no hits, while generation/active-state and archive/event guards produced live code buckets that are now assigned to downstream cleanup children P417-P419 and final verification P420.

## Done

- Created `.complex-problems/L20260516-222011/tmp/p416/`.
- Captured Cortex-ish repo paths.
- Ran targeted guards over `novaic-cortex` plus Cortex-facing runtime bridge files:
  - generation / active-state guard.
  - default / fallback guard.
  - archive / diagnostic / context-event guard.
- Bucketed guard hits by file.
- Split live source files from tests and non-live guard/docs files.
- Produced `live-surface-map.md` assigning live surfaces to downstream children.

## Verification

- `cortex-default-fallback-guard.txt`: 1 line, header only.
- `cortex-generation-active-guard.txt`: 271 lines.
- `cortex-archive-event-guard.txt`: 1173 lines.
- `file-buckets.txt` summarizes high-volume files.
- `live-source-files.txt`, `test-files.txt`, and `non-live-files.txt` separate live code from tests/docs.
- No source code was changed in this inventory ticket.

## Known Gaps

The inventory identified live risk candidates for downstream cleanup:

- `ScopeEndRequest` can accept calls without archive diagnostics.
- `get_active_stack()` / `read_active_stack_projection()` use generation `0` as an absent-row sentinel.
- Workspace archive projection still walks files for debug/archive projection and needs live-path verification.
- Cortex handler meta-read soft-fail should remain trace-only and must not weaken required generation/finalize validation.

These are owned by P417-P419 and final P420 verification, not closed by P416 itself.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p416/cortex-ish-paths.txt`
- `.complex-problems/L20260516-222011/tmp/p416/cortex-generation-active-guard.txt`
- `.complex-problems/L20260516-222011/tmp/p416/cortex-default-fallback-guard.txt`
- `.complex-problems/L20260516-222011/tmp/p416/cortex-archive-event-guard.txt`
- `.complex-problems/L20260516-222011/tmp/p416/file-buckets.txt`
- `.complex-problems/L20260516-222011/tmp/p416/live-source-files.txt`
- `.complex-problems/L20260516-222011/tmp/p416/test-files.txt`
- `.complex-problems/L20260516-222011/tmp/p416/non-live-files.txt`
- `.complex-problems/L20260516-222011/tmp/p416/live-surface-map.md`
