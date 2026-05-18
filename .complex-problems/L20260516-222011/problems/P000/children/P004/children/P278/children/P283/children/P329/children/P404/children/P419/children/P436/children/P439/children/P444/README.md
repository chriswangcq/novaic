# Context task handler projection contract cleanup

## Problem

The `context.read` task handler both reads materialized context and appends notification hints. Its contract must be explicit so future code does not treat it as LLM history assembly.

## Success Criteria

- `context.read` handler docs/names/tests state it is notification/projection maintenance, not LLM prepare.
- Notification hint idempotency behavior remains covered.
- Assistant/system context append behavior remains covered.
- Focused context handler tests pass.
