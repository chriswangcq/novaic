# ContextEvent API lifecycle endpoint cleanup

## Problem

ContextEvent API endpoints that append or prepare context may contain lifecycle compatibility logic that bypasses the event-source model.

## Success Criteria

- Inspect API endpoints that call `ContextEventWriter`, prepare LLM context, write context messages, attach inputs, or close skills.
- Ensure they pass explicit identity and do not infer stale active state from old file layouts.
- Patch dangerous defaulting or hidden lookup behavior if found.
- Add focused API lifecycle tests for changed behavior.
- Run context event API lifecycle/write tests.

