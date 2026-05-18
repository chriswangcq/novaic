# Patch session repo state reconstruction generation validation

## Problem Definition

`SessionRepository` reconstructs runtime state from active/session dictionaries with raw `int(... or 0)`, which can hide malformed generation values before dispatch/finalize decisions.

## Proposed Solution

Add a small helper that validates runtime-state generation by status: `NO_ACTIVE` may use generation `0`, while active-like states require positive generation. Use it in `_decide_live_dispatch` and `_runtime_state_from_session_state`, and add focused tests for malformed active generation.

## Acceptance Criteria

- Raw generation defaults are removed from session repo runtime reconstruction paths.
- No-active generation `0` still works.
- Active state malformed/bool generation fails loudly.
- Focused session repo/attach/finalize tests pass.

## Verification Plan

Run compile check for `session_repo.py`, focused session repo/generation tests, and targeted source guard.

## Risks

- Tests may construct minimal state dicts with generation `0`; helper must only require positive generation for non-no-active statuses.

## Assumptions

- Any persisted active-like state with missing or invalid generation is corrupt and should not be silently accepted.
