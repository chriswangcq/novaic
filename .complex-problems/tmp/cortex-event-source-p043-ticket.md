# Remove runtime structural scope bypass

## Problem Definition

`Cortex.scope_create` and `Cortex.scope_end` still expose direct runtime lifecycle helpers that call Workspace structural writes without going through the event-wired API helpers. They are not the active queue-service path, but their existence keeps a bypass available and keeps old tests attached to the wrong abstraction.

## Proposed Solution

- Physically remove `Cortex.scope_create` and `Cortex.scope_end` from `novaic_cortex/runtime.py`.
- Rewrite tests that use those methods to either:
  - call the event-wired API request handlers (`scope_create`, `scope_end`) where lifecycle behavior is still valid to test, or
  - become guard tests asserting the runtime façade no longer exposes those lifecycle helpers.
- Preserve runtime façade responsibilities for agent-facing tools (`tool_read`, `tool_write`, `tool_shell`) and skill installation only.
- Run static scans to prove no remaining code calls `cortex.scope_create(...)` or `cortex.scope_end(...)`.
- Run focused migrated tests and then the full Cortex suite.

## Acceptance Criteria

- `novaic_cortex/runtime.py` no longer defines `scope_create` or `scope_end`.
- No active test or runtime code calls `cortex.scope_create(...)` or `cortex.scope_end(...)`.
- Lifecycle tests use API/context paths or guard removal explicitly.
- No runtime direct structural lifecycle helper can bypass ContextEvent writers.
- Full Cortex suite passes.

## Verification Plan

- Static scan:
  - `rg -n "def scope_(create|end)|\\.scope_create\\(|\\.scope_end\\(" novaic_cortex tests`
- Run focused migrated/guard tests touched by the ticket.
- Run full Cortex suite with sibling dependency `PYTHONPATH`.

## Risks

- Several older tests use runtime lifecycle helpers for convenience and may need careful rewriting to avoid weakening coverage.
- Hook/metric tests may be testing behavior that becomes obsolete once lifecycle helpers are removed; those should be converted to tool-facing or guard-level coverage rather than kept through compatibility shims.

## Assumptions

- Queue-service active lifecycle path uses Cortex API handlers, not `Cortex.scope_create/end`.
- This ticket is allowed to delete compatibility behavior because the user requested full cutover and no backwards compatibility.
