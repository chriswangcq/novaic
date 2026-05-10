# Verify Runtime Stack Read Cutover

## Problem Definition

After P031/P032/P033, Phase 3C needs a final gate proving `context_status`, `skill_begin`, and `skill_end` control reads use SQLite active-stack projection and that remaining file-walk stack usage is explicitly deferred to P020.

## Proposed Solution

- Run targeted status/begin/end/active-stack tests.
- Run static source audit over the relevant API endpoint sections.
- Confirm `context_status`, `skill_begin`, and `skill_end` use `read_active_stack_projection`.
- Confirm successful begin/end control paths do not call `resolve_active_scope_path`.
- List remaining `_collect_active_stack` and `resolve_active_scope_path` usages by owner/scope.
- Run full Cortex tests.

## Acceptance Criteria

- Targeted status/begin/end cutover tests pass.
- Static audit proves status/begin/end runtime control reads use SQLite adapter.
- Remaining file-walk usage is documented and assigned to P020 or non-runtime surfaces.
- Full Cortex tests pass.

## Verification Plan

- Use `rg` and focused section extraction.
- Run targeted test files.
- Run full `novaic-cortex/tests`.

## Risks

- Static grep can be too coarse; inspect sections enough to distinguish success path from error/future cleanup.

## Assumptions

- P034 is a verification gate, not a cleanup ticket. Cleanup belongs to P020.
