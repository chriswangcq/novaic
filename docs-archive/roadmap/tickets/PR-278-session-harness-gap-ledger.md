# PR-278 — Session Harness Gap Ledger

Status: Closed

## Goal

Record the remaining gap list between the ideal session harness architecture
and the current implementation after PR-277.

## Scope

- Add a durable architecture ledger that names current good shape, remaining
  gaps, and explicit non-gaps.
- Keep the ledger focused on harness state-machine infrastructure, not LLM
  behavior.

## Acceptance Criteria

- A single architecture file lists all current executable gaps.
- The file distinguishes true gaps from things that should not move into FSM.
- Follow-up tickets PR-279 through PR-282 reference the gaps.

## Verification

- Manual read of `docs/architecture/session-harness-ideal-gap-ledger.md`.

## Closure Notes

- Added `docs/architecture/session-harness-ideal-gap-ledger.md`.
- Recorded five remaining executable gaps and explicit non-gaps.
- Created follow-up tickets PR-279 through PR-282.
