# Session repo state reconstruction validation

## Problem

`session_repo.py` uses raw defaults when converting active/session state dictionaries into `SessionRuntimeState`. These conversions feed dispatch/finalize decisions and should explicitly distinguish no-active generation `0` from malformed active-state generation.

## Success Criteria

- Runtime state reconstruction validates active/ending/recovering/suspected-dead generation explicitly.
- No-active state still permits generation `0`.
- Focused session repo/FSM tests cover malformed active generation rejection.
- Targeted guard no longer reports unclassified repo reconstruction generation defaults.
