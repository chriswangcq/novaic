# Sandbox Service SDK Compatibility Residue Inventory Result

## Summary

Closed the sandbox service/SDK compatibility residue inventory. The audit split service execution, SDK/client boundary, and wire/base64/mount ownership. All children closed successfully with static scan artifacts, classifications, and focused tests.

## Done

- P620 audited sandbox-service/core execution boundary. The internal process runner and mount namespace helper are intended sandboxd internals, with no active local fallback/bypass found.
- P621 audited SDK/client/runtime call boundaries. The SDK is a thin HTTP/DTO client, runtime delegates shell execution through Cortex, and no active runtime user-shell bypass remains.
- P622 audited stdout/stderr base64 and mount/path residue. Base64 is wire/durable/current-perception only, not public history text; mount ownership is SDK DTO -> Cortex LogicalFS -> sandboxd namespace execution.

## Verification

- P620 check C653 succeeded; sandbox-service focused tests: 13 passed.
- P621 check C659 succeeded; SDK tests: 3 passed; SDK+Cortex: 38 passed; runtime: 55 passed; runtime shell wrapper/path-contract focused tests also passed in child evidence.
- P622 check C662 succeeded; base64/projection Python tests: 50 passed; frontend monitor redaction tests: 18 passed; mount/logicalfs tests: 24 passed.

## Boundary Decision

Sandboxd remains the only process execution service. LogicalFS supplies the mounted file view. SDK DTOs and Cortex shell delegation do not create a legacy execution path, and current shell/device artifacts do not publish raw binary bytes into public LLM/tool history.

## Residual Risk

- Legacy inline image parser compatibility remains in `step_result_projection.py`, but it is classified as old-reader compatibility and current artifact/BlobRef paths are guarded by tests.
- Generated local `__pycache__` files remain for final workspace hygiene.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p620-service-classification.md`
- `.complex-problems/L20260516-222011/tmp/p623-sdk-classification.md`
- `.complex-problems/L20260516-222011/tmp/p624-result.md`
- `.complex-problems/L20260516-222011/tmp/p625-coverage-classification.md`
- `.complex-problems/L20260516-222011/tmp/p628-base64-history-classification.md`
- `.complex-problems/L20260516-222011/tmp/p629-mount-boundary-classification.md`
