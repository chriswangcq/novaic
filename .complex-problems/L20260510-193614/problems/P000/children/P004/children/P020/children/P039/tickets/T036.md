# Delete File-Walk Active Stack Helper And Add Final Guards

## Problem Definition

After P035-P038, the only remaining active-stack file-walk residue in `api.py` is wake creation projection seeding plus the `_collect_active_stack(...)` helper itself. Leaving the helper and residual wake seeding in place risks future code reusing filesystem stack walking as authority.

## Proposed Solution

Make active-stack projection writes self-contained for root/wake creation and remove the file-walk helper:

- Replace wake `scope_create` idempotent and new-create projection seeding with a deterministic wake frame derived from `root_scope_path`, `existing_path` or newly-created `path`, and request metadata.
- Stop calling `_collect_active_stack(...)` in `scope_create`.
- Delete `_collect_active_stack(...)` from `api.py` if no references remain.
- Add/strengthen static guards asserting `_collect_active_stack` is absent from `api.py`.
- Add tests proving root/wake creation seeds SQLite active-stack projection without file-walk and works after monkeypatching any old helper name if necessary.
- Run full Cortex tests and static grep audit.

## Acceptance Criteria

- `api.py` has no `_collect_active_stack(...)` function or call sites.
- `api.py` has no `resolve_active_scope_path(...)` references.
- Root creation still projects an empty active stack.
- Wake creation and idempotent wake creation project the wake frame into SQLite active-stack state.
- Static guards fail if file-walk active-stack authority is reintroduced.
- Targeted tests and full Cortex test suite pass.

## Verification Plan

- Run static audit:
  - `rg -n "_collect_active_stack|resolve_active_scope_path" novaic-cortex/novaic_cortex/api.py -S`
- Run targeted tests:
  - active-stack projection helper;
  - skill lifecycle;
  - scope create/wake/status behavior;
  - read-source guards;
  - active write routing.
- Run full Cortex test suite.

## Risks

- Wake creation idempotency must preserve the current active-stack frame shape for existing active wake paths.
- If old tests created multiple wake scopes as active siblings, projection should still point to the latest wake created by the public endpoint.

## Assumptions

- Root/wake `scope_create` is the public lifecycle path responsible for initializing stack projection before runtime skill operations.
- No compatibility path may silently fall back to filesystem active-stack walking.
