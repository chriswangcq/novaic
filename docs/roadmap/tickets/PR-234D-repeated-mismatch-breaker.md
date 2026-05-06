# PR-234D — Repeated Mismatch Breaker And Force-Finalize Semantics

| Field | Value |
| --- | --- |
| Status | `[x]` |
| Parent | PR-234 |
| Scope | `novaic-agent-runtime` |

## Current State

When the LLM repeats the same invalid `skill_end(scope_id=...)`, Runtime can continue to another think round until the round cap forces finalization. The current round-cap branch also returns `stack_empty:true`, which conflates natural stack closure with forced recovery.

## Objective

Add a deterministic repeated-error breaker and make force-finalize decisions explicit.

## Small Tickets

- `[x]` Compute a stable fingerprint for repeated tool logical failures, especially `skill_end` `scope_mismatch`.
- `[x]` Carry retry state explicitly through ReactActions → ReactThink context.
- `[x]` Force finalize after the configured repeated mismatch threshold.
- `[x]` Change decision output to distinguish `should_finalize` from `stack_empty`.
- `[x]` Update saga branch conditions and tests.

## Acceptance Criteria

- Same `skill_end` mismatch cannot repeat until round cap.
- `round_cap` and `repeated_scope_mismatch` are recorded as explicit `force_finalize_reason` values.
- `stack_empty` means natural empty stack only.

## Verification

- `cd novaic-agent-runtime && pytest tests/test_pr48_turn_finalizer.py tests/test_pr234_repeated_scope_mismatch.py`
