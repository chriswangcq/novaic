# Sandbox Mount Ownership and Bypass Residue Result

## Summary

Classified mount ownership across SDK, Cortex LogicalFS, sandbox-service internals, and runtime. No client-side/runtime mount bypass was found; mount responsibility is layered as SDK DTO, Cortex planning, and sandboxd service-internal namespace execution.

## Done

- Recorded exact mount scan in `.complex-problems/L20260516-222011/tmp/p629-mount-boundary-scan.txt`.
- Captured representative SDK/Cortex/service/test slices in `.complex-problems/L20260516-222011/tmp/p629-mount-boundary-slices.txt`.
- Wrote ownership classification in `.complex-problems/L20260516-222011/tmp/p629-mount-boundary-classification.md`.
- Ran focused SDK/service/Cortex mount/logicalfs tests.

## Verification

- `python -m pytest novaic-sandbox-sdk/tests/test_sandbox_sdk.py novaic-sandbox-service/tests novaic-cortex/tests/test_sandboxd_wiring.py novaic-cortex/tests/test_sandbox_requires_mount_namespace.py -q` passed: 24 tests.

## Known Gaps

- None blocking. Host and mount terms are expected in tests and service internals.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p629-mount-boundary-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p629-mount-boundary-slices.txt`
- `.complex-problems/L20260516-222011/tmp/p629-mount-boundary-classification.md`
- `.complex-problems/L20260516-222011/tmp/p629-mount-boundary-tests.txt`
