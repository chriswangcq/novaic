# Ticket: Scope End Boundary Contract Propagation

## Problem Definition

`wake_finalize` builds explicit archive diagnostics and `handle_cortex_scope_end` validates positive `session_generation`, but `CortexBridge.scope_end` and `ScopeEndRequest` currently drop those fields. The boundary must carry explicit diagnostics into Cortex before persistence can be fixed.

## Proposed Solution

Extend `CortexBridge.scope_end` to accept and post explicit `session_generation`, `finalize_reason`, `remaining_stack`, and `round_num` fields. Update `handle_cortex_scope_end` to normalize and forward those diagnostics. Extend `ScopeEndRequest` to accept the same fields with explicit positive-generation validation for finalize diagnostic archive requests. Add/update focused runtime tests proving bridge call kwargs/payload forwarding and Cortex request validation.

## Acceptance Criteria

- Runtime handler forwards `session_generation`, `finalize_reason`, remaining-stack diagnostics, and `round_num` to `bridge.scope_end`.
- `CortexBridge.scope_end` includes those fields in the `/v1/scope/end` request payload when supplied.
- `ScopeEndRequest` accepts the explicit diagnostics fields.
- Missing or non-positive generation is still rejected before archive through the runtime handler and by Cortex request validation when diagnostics are present.
- Existing neutral structural scope-end callers remain valid without hidden inference.
- Focused runtime/Cortex contract tests pass.

## Verification Plan

- Update and run runtime tests around `handle_cortex_scope_end`.
- Add or update bridge-level test for posted payload.
- Add or update Cortex request validation test for `ScopeEndRequest`.
- Run `python3 -m py_compile` for changed runtime bridge/handler and Cortex API modules.

## Risks

- Fake bridges in existing tests may have narrow signatures and need explicit updates.
- Making all Cortex structural scope-end calls require generation could break non-runtime tests; keep the strict generation requirement tied to supplied finalize diagnostics while runtime handler remains strict.

## Assumptions

- P373 owns persistence semantics; this ticket only ensures Cortex receives the explicit diagnostics contract.
