# Remove dead runtime scope lifecycle metrics coverage

## Problem

`CortexMetrics.scopes_created` and `scopes_archived` were incremented only by removed runtime lifecycle helpers. Tests still assert those counters, which preserves an obsolete runtime ownership model.

## Success Criteria

- Runtime metrics tests no longer assert scope lifecycle counters.
- If no production code owns these counters after runtime helper removal, `CortexMetrics` removes the dead fields and tests are updated accordingly.
- `tests/test_wave4_metrics.py`, remaining metrics assertions in `tests/test_hooks_limits.py`, and metric shape tests pass.
