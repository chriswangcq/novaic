# Workspace hook test migration check

## Summary

Success. Hook tests now exercise the Workspace lifecycle projection emitter directly and no longer use removed runtime lifecycle helpers.

## Evidence

- Static scan of the hook test files found no `.scope_create(` or `.scope_end(` calls.
- Focused hook tests passed: `7 passed in 0.08s`.

## Criteria Map

- `tests/test_hooks_metrics.py` no longer calls runtime lifecycle helpers: satisfied.
- Hook-focused cases in `tests/test_hooks_limits.py` no longer call runtime lifecycle helpers: satisfied.
- Hook behavior remains covered through Workspace lifecycle/projection methods: satisfied.
- Focused hook tests pass: satisfied.

## Execution Map

- R040 rewrote hook tests to `create_scope_projection` / `archive_root_scope_projection`.
- R040 removed obsolete runtime scope metric assertions from hook-emission tests.

## Stress Test

- The check used exact static scan patterns for the removed runtime helper calls and ran the affected focused tests.

## Residual Risk

- Dead runtime scope lifecycle metric fields remain tracked by P053.

## Result IDs

- R040
