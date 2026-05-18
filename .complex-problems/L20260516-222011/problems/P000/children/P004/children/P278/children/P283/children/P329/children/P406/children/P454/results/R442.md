# T446 Result: Aggregate compatibility focused behavior tests

## Summary

Focused compatibility behavior verification passed across both runtime and Cortex. Runtime selected suite passed with `100 passed`; Cortex selected suite passed with `135 passed`. Logs and exit statuses are saved under the P456/P457 artifact directories.

## Child Results

- P456 / R440 / C466: runtime focused compatibility behavior tests passed.
- P457 / R441 / C467: Cortex focused compatibility behavior tests passed.

## Evidence

- Runtime log: `.complex-problems/L20260516-222011/tmp/p456/runtime-focused-tests.log`
- Runtime exit: `.complex-problems/L20260516-222011/tmp/p456/runtime-focused-tests.exit` = `0`
- Runtime summary: `100 passed in 0.59s`
- Cortex log: `.complex-problems/L20260516-222011/tmp/p457/cortex-focused-tests.log`
- Cortex exit: `.complex-problems/L20260516-222011/tmp/p457/cortex-focused-tests.exit` = `0`
- Cortex summary: `135 passed in 1.95s`

## Coverage Map

- Runtime attach/finalize/session-ended/recovery/session-state/generation guards: covered by P456.
- Runtime shell output and no historical tool-image injection contracts: covered by P456.
- Cortex archive/context/event/payload/shell compatibility guards: covered by P457.
- Cortex projection/store/no-compat/legacy lifecycle removal guards: covered by P457.

## Changes

No source changes were made by this aggregate ticket. It only split, ran, and recorded focused behavior tests.

## Residual Risk

No focused behavior failures remain in the selected suites. Parent P406 still needs its final aggregate result/check to combine the scan classification and behavior verification.
