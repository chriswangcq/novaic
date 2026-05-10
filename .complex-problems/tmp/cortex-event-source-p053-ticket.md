# Remove dead runtime scope lifecycle metrics

## Problem Definition

`CortexMetrics.scopes_created` and `CortexMetrics.scopes_archived` were owned by the now-removed runtime lifecycle helpers. Keeping those fields makes runtime metrics claim ownership over lifecycle transitions it no longer performs.

## Proposed Solution

- Remove `scopes_created` and `scopes_archived` from `CortexMetrics`.
- Update metrics shape tests to construct/assert only live runtime-owned metrics.
- Update `tests/test_wave4_metrics.py` so it covers `skills_installed` and other runtime-owned metrics, not structural archival counters.
- Update chaos tests to use Workspace projection setup for scope churn and assert read/write metrics only.
- Keep service/API Prometheus metrics such as `cortex_scopes_archived_total` untouched because they belong to the API/observability layer, not `CortexMetrics`.

## Acceptance Criteria

- Static scan shows no `scopes_created` or `scopes_archived` in `novaic_cortex/types.py` or runtime metric tests.
- `CortexMetrics` contains only runtime-owned counters.
- Focused metrics/chaos tests pass.

## Verification Plan

- Static scan:
  - `rg -n "scopes_created|scopes_archived" novaic_cortex/types.py tests/test_cortex_chaos.py tests/test_wave4_metrics.py tests/test_hooks_limits.py`
- Run focused tests:
  - `pytest tests/test_cortex_chaos.py tests/test_wave4_metrics.py tests/test_hooks_limits.py -q`

## Risks

- Some docs or observability comments may still mention service-level scope metrics; those are not the same object and should not be removed blindly.

## Assumptions

- Runtime-owned `CortexMetrics` should not include lifecycle counters after lifecycle is event/API-owned.
