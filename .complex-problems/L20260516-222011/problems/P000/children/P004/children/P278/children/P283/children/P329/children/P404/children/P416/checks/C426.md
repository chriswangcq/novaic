# Check P416 against R400

## Verdict

success

## Skeptical Review

This was a one_go ticket, so I checked whether it actually produced an actionable map rather than just raw grep output. R400 includes guard files, file buckets, live/test/non-live separation, and concrete downstream ownership for risk candidates.

## Criteria Review

- Run Cortex-specific guards: satisfied by three saved guard files.
- Save guard outputs under ledger tmp: satisfied under `.complex-problems/L20260516-222011/tmp/p416/`.
- Classify files into live code, tests, migration/scripts, docs/history, generated/cache exclusions: satisfied by `live-source-files.txt`, `test-files.txt`, `non-live-files.txt`, and exclusions recorded in `live-surface-map.md`.
- Produce live-surface map for downstream children: satisfied by `live-surface-map.md`.
- Create further split if unexpectedly broad: downstream children P417-P420 already exist and own the identified live slices; no additional blocking split is needed for inventory.

## Stress Test

The archive/event guard is large (`1173` lines), so raw match count alone is not meaningful. The check treats success as structured classification and downstream ownership, not zero output.

## Residual Risk

Inventory found real candidates but did not fix them. That is acceptable for P416 because P417-P419 own cleanup and P420 owns final verification.

## Evidence

- `.complex-problems/L20260516-222011/tmp/p416/live-surface-map.md`
- `.complex-problems/L20260516-222011/tmp/p416/file-buckets.txt`
- `.complex-problems/L20260516-222011/tmp/p416/cortex-default-fallback-guard.txt`
- `.complex-problems/L20260516-222011/tmp/p416/cortex-generation-active-guard.txt`
- `.complex-problems/L20260516-222011/tmp/p416/cortex-archive-event-guard.txt`
