# Migrate hooks and metrics lifecycle tests

## Problem

Hook and metric tests are coupled to removed runtime lifecycle helpers. Some assertions may represent obsolete runtime-hook behavior rather than live event-wired lifecycle behavior, so this family needs careful rewrite or deletion rather than compatibility restoration.

## Success Criteria

- `tests/test_hooks_metrics.py`, `tests/test_hooks_limits.py`, and `tests/test_wave4_metrics.py` no longer call `cortex.scope_create(...)` or `cortex.scope_end(...)`.
- Obsolete runtime lifecycle hook assertions are removed or replaced with relevant runtime/tool/API-facing coverage.
- Focused hooks/metrics tests pass.
