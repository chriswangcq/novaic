# Migrate runtime lifecycle helper tests

## Problem

Multiple older tests call `cortex.scope_create(...)` or `cortex.scope_end(...)` for convenience. Once runtime lifecycle helpers are removed, those tests must be rewritten to the event-wired API path or converted to guard/obsolete behavior tests without preserving the bypass.

## Success Criteria

- No test uses `cortex.scope_create(...)` or `cortex.scope_end(...)`.
- Tests that still need lifecycle setup use `novaic_cortex.api.scope_create` / `scope_end` request handlers or lower-level projection helpers only when explicitly testing projections.
- Obsolete hook/metric expectations tied only to runtime lifecycle helpers are removed or replaced with relevant tool-facing/API-facing assertions.
- Focused migrated test files pass.
