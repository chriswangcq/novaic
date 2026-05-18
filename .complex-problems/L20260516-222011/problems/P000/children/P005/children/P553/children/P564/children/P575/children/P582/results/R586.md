# Result: Display history and perception regression inventory closed

## Summary

The display regression inventory was split into four independent contracts and all succeeded with exact scans, line-cited tests, and focused pytest runs. The project now has explicit test coverage for current display perception, historical text-only replay, durable no-base64 output, and active-stack/system-message ordering.

## Done

- Closed P593 / R579: current-round display image injection selects `display_perception` and resolves BlobRef `image_ref` into provider image content.
- Closed P594 / R580: historical display replay uses `history`, avoids Blob fetches, and does not create user image messages.
- Closed P595 / R584: durable shell/display output base64 absence is covered across shell CLI, display handler, and Cortex projection.
- Closed P596 / R585: active-stack/system-message ordering keeps current display perception working and downgrades non-current display to history.

## Verification

- P593 focused tests: `3 passed in 0.07s`.
- P594 focused tests: `3 passed in 0.05s`.
- P595 split children focused tests: 10 passed total.
- P596 focused tests: `4 passed in 0.05s`.
- Total focused tests represented by this inventory: 20 passing tests.

## Known Gaps

- None for the display history/perception regression inventory.
- Broader full-suite unrelated failures, if any, are outside this inventory and were not used to weaken these focused contract results.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p593/current-display-injection-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p594/history-replay-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p595-result.md`
- `.complex-problems/L20260516-222011/tmp/p596/active-stack-ordering-scan.txt`
