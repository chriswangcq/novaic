# Rewrite hook tests to Workspace projection emitter

## Problem

Hook tests currently call removed runtime lifecycle helpers even though `on_scope_created` and `on_scope_archived` are emitted by Workspace lifecycle projection methods. They should test the emitter directly without runtime bypasses.

## Success Criteria

- `tests/test_hooks_metrics.py` and hook-focused cases in `tests/test_hooks_limits.py` no longer call `cortex.scope_create(...)` or `cortex.scope_end(...)`.
- Hook success/failure/isolation behavior is still covered using Workspace lifecycle/projection methods.
- Focused hook tests pass.
