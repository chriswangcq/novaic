# PR-299 — Session Ledger Required Interface

Status: Closed

## Goal

Remove optional capability detection from the session coordinator. The session
repository must receive a ledger with the complete current interface.

## Scope

- Delete `hasattr(..., "list_active_states")` fallback logic.
- Keep `session_state` as the SSOT for active session listings.
- Add or update a guard test proving the fallback branch is gone.

## Dependencies

- PR-272 session active-state ledger boundary.

## Risks

- Hand-written test doubles missing ledger methods will fail. This is desired:
  fakes must match the explicit boundary.

## Acceptance Criteria

- No active runtime code probes ledger capabilities with `hasattr`.
- Active session listing calls the ledger interface directly.
- Runtime tests pass.

## Verification

- Grep for the removed fallback.
- Targeted residue guard.
- Full runtime suite.

## Closure Notes

- Removed the `hasattr(self.session_ledger, "list_active_states")` fallback from
  `SessionRepository.list_active_sessions()`.
- Updated the strict input-ledger test fake to implement the required ledger
  boundary instead of relying on optional capability detection.
- Added a residue guard that fails if the fallback returns.
- Verified by targeted residue tests and full runtime suite:
  `pytest` in `novaic-agent-runtime` -> 364 passed.
