# Runtime scope lifecycle metrics cleanup result

## Summary

Removed dead runtime scope lifecycle counters from `CortexMetrics` and updated metrics tests to cover only runtime-owned counters.

## Done

- Removed `scopes_created` and `scopes_archived` from `CortexMetrics`.
- Updated `tests/test_cortex_chaos.py` to stop constructing/asserting dead scope counters and to use `workspace.create_scope_projection` for scope churn setup.
- Updated `tests/test_wave4_metrics.py` to cover `skills_installed` plus runtime-owned file read/write metrics.
- Confirmed hook-limit tests no longer assert removed scope counters.

## Verification

- Static scan:
  - `rg -n "scopes_created|scopes_archived" novaic_cortex/types.py tests/test_cortex_chaos.py tests/test_wave4_metrics.py tests/test_hooks_limits.py`
  - Result: no matches.
- Focused tests:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_cortex_chaos.py tests/test_wave4_metrics.py tests/test_hooks_limits.py -q`
  - Result: `10 passed in 0.10s`

## Known Gaps

- Service/API-level Prometheus names such as `cortex_scopes_archived_total` remain intentionally untouched because they are not `CortexMetrics` runtime façade counters.

## Artifacts

- Changed: `novaic-cortex/novaic_cortex/types.py`
- Changed: `novaic-cortex/tests/test_cortex_chaos.py`
- Changed: `novaic-cortex/tests/test_wave4_metrics.py`
