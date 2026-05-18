# Normalize session repo and ledger generation adapters

## Problem Definition

Session repo and session ledger still contain raw generation defaults in state reconstruction and ledger generation helpers. Some may be DB adapter normalization, but some feed authority decisions and should reject malformed state instead of defaulting.

## Proposed Solution

Audit the remaining `session_repo.py` and `session_ledger.py` generation hits, patch live authority paths to use explicit positive/non-negative validators, and classify truly internal DB adapters with focused tests or evidence.

## Acceptance Criteria

- `_decide_live_dispatch` and `_runtime_state_from_session_state` use explicit generation validation appropriate to no-active vs active states.
- Session ledger generation increment/read helpers are either explicit validators or classified safe with tests.
- Focused session repo/ledger tests pass.
- Guard output for repo/ledger generation hits is clean or fully classified.

## Verification Plan

Run compile checks, focused session repo/generation attach/finalize tests, and targeted `rg` guards for session repo/ledger generation patterns.

## Risks

- State reconstruction must still allow `NO_ACTIVE` generation `0`.
- Active states should require positive generation.

## Assumptions

- Malformed persisted active session generation should fail loudly rather than silently route inputs.
