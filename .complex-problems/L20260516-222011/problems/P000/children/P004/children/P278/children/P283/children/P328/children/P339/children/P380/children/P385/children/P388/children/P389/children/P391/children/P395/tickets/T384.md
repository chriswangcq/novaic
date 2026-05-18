# Patch session ledger generation helpers

## Problem Definition

`SessionLedgerRepository.session_generation` and `next_generation` still use raw `int(current.get("generation") or 0)`, which makes ledger authority helpers look like they silently default malformed state.

## Proposed Solution

Add an explicit non-negative generation helper in `session_ledger.py`, use it in both helper methods, and add focused tests with monkeypatched malformed ledger state to prove bool/invalid values are rejected.

## Acceptance Criteria

- No raw `int(current.get("generation") or 0)` remains in `session_ledger.py`.
- `session_generation` and `next_generation` reject bool/malformed current generation.
- Existing session ledger tests pass.

## Verification Plan

Run compile check for `session_ledger.py`, focused session ledger tests, and targeted source guard.

## Risks

- Real SQLite rows generally return integers; malformed-state tests may need to monkeypatch `get_state` to exercise adapter validation directly.

## Assumptions

- Missing state remains valid and maps to generation `1` for active scope creation or `0` when no active scope exists.
