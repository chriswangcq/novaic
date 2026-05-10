# Phase 5D.2 Guard Coverage Review And Tightening

## Problem Definition

Review whether removed local-authority and compatibility paths are protected by durable tests or static guards. If a high-risk removed path can return without test/static failure, add the smallest guard.

## Proposed Solution

- Inspect current tests for:
  - scope lookup uniqueness via SQLite `scope_projection`
  - active stack projection and LIFO reads
  - removed step formatting public `include_display` API
  - temp sandbox backing path rejection
  - Redis scope lock fail-closed / in-memory test-only boundary
  - removed `format_for_llm` public compatibility wrapper
- Run or add narrow tests where gaps are found.
- Avoid adding broad brittle grep tests when a focused unit/API test already guards the behavior.

## Acceptance Criteria

- Guard coverage map is recorded for each high-risk removed path.
- Any missing high-value guard is added or a follow-up problem is created.
- New or affected tests pass.

## Verification Plan

```bash
rg -n "scope_projection|already used|unsupported_step_projection|include_display|novaic-cortex-sandbox-|RedisScopeLockManager|format_for_llm|resolve_for_llm" novaic-cortex/tests novaic-agent-runtime/tests -S
pytest -q <targeted guard tests>
```

## Risks

- Adding purely textual grep tests can become noisy; prefer behavioral tests where possible.
- Some guards may already exist under different names; inspect before adding.

## Assumptions

- This ticket is allowed to add small targeted tests/static guards, but not broad runtime rewrites.
