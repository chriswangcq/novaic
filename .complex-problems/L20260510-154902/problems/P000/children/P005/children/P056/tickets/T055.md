# Cut status usage and stack reads to event semantics

## Problem Definition

`context_status(include_usage=True)` still renders via the DFS `ContextEngine`, and default status stack still comes from `_collect_active_stack`. After P055, the primary LLM prepare path is event-projection backed; status must now follow the same event semantics for usage, while any remaining filesystem stack traversal must be explicitly treated as operational control validation only.

## Proposed Solution

Update status handling so:

- `context_status(include_usage=True)` uses `ContextEventReadModel` for messages, token estimate, usage ratio, and projected stack/status.
- `context_status(include_usage=False)` can continue to use `_collect_active_stack` only as a fast operational/control-plane stack check, with documentation and tests making that boundary explicit.
- Event-authored tests cover `include_usage=True` returning projected stack and usage values.
- No DFS fallback remains in the status usage path.

Do not delete `_collect_active_stack` yet; P057 will do the broad DFS/fallback cleanup audit.

## Acceptance Criteria

- `context_status(include_usage=True)` does not import or instantiate `ContextEngine`.
- The include-usage status path returns event-projected stack frames, total messages, estimated tokens, and usage ratio.
- Default status path remains documented as operational control stack if still present.
- Focused tests prove include-usage status uses event-authored state.
- Static scan classifies remaining `_collect_active_stack` references outside LLM/status usage source.

## Verification Plan

- Run focused status tests.
- Run static scan around `context_status` for `ContextEngine`.
- Run full Cortex tests.

## Risks

- Runtime may depend on fast default status being cheap; keep default path cheap for now.
- API consumers may assume default status and include-usage status stack shapes match. The adapter already normalizes stack top-first for compatibility.

## Assumptions

- Event projection is now the authoritative source for prepared messages and usage metrics.
- `_collect_active_stack` is acceptable only for operational control/LIFO validation until the next cleanup ticket removes or narrows it further.
