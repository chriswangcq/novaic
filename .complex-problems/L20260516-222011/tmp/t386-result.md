# Audit and projection generation classification result

## Summary

Classified and tightened audit/projection generation handling. Read-only audit DTOs now use explicit non-negative parsing helpers and reject bool generation values instead of relying on raw `int(... or 0)`.

## Done

- Patched `queue_service/session_audit.py` with `_audit_generation`.
- Patched `queue_service/queue_audit.py` with `_required_non_negative_int`.
- Added focused tests rejecting bool generation in session audit and queue FSM audit.
- Classified remaining audit/projection hits:
  - `queue_audit.py` helper usages are safe explicit audit parsing.
  - `session_audit.py` helper internal `int(value)` is safe after bool/missing/non-negative checks.
  - `session_observed_events.py` internal `int(value)` is safe positive-generation validation for observed wake-created effects.

## Verification

- `python3 -m py_compile queue_service/session_audit.py queue_service/queue_audit.py` passed.
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr295_session_audit_tooling.py tests/test_pr314_queue_control_plane_audit_replay.py` passed: 8 tests.
- Targeted audit/projection guard now shows only explicit helper usages or validation helper internals.

## Known Gaps

- Generic task/saga/lease FSM counter classification remains for P397.

## Artifacts

- Patched files: `novaic-agent-runtime/queue_service/session_audit.py`, `novaic-agent-runtime/queue_service/queue_audit.py`, `novaic-agent-runtime/tests/test_pr295_session_audit_tooling.py`, `novaic-agent-runtime/tests/test_pr314_queue_control_plane_audit_replay.py`.
