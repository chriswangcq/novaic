# P003 Success Check - Cortex registry 显式依赖边界收口

## Summary
P003 is successful. The Cortex registry no longer hides environment or clock reads in its constructor; production defaults are resolved in a named boundary factory.

## Evidence
- Constructor signature requires `payload_blob_policy` and `clock`.
- Constructor test fails if `BlobPayloadPolicy.from_env()` or `time.time()` is called.
- `build_workspace_registry()` is the only registry production helper that resolves env/time defaults.
- `main_cortex.py` uses the helper.

## Criteria Map
- No `BlobPayloadPolicy.from_env()` in constructor: met.
- No `time.time` default in constructor: met.
- Production wiring still clear: met via `build_workspace_registry()`.
- Tests verify explicit deterministic constructor: met.

## Execution Map
- Refactored registry constructor.
- Added boundary factory.
- Updated main wiring.
- Added tests.

## Stress Test
Registry dependency tests plus existing workspace tests passed together.

## Residual Risk
`Workspace` still allows default `clock or time.time`; this ticket scoped the registry boundary. A global Cortex hidden-input cleanup can address workspace defaults if required.
