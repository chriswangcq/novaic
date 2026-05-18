# Recovery and session-ended contract inventory

## Problem

Before changing recovery code, inspect suspected-dead, recovery archive, session-ended, and finalize-adapter production paths. Classify whether they preserve explicit generation and stack diagnostics, and identify silent fallback behavior.

## Success Criteria

- Production paths in `saga_repo.py`, `session_recovery.py`, `session_repo.py`, `session_fsm.py`, and `session_handlers.py` are inspected.
- Raw guard and classified artifacts are saved.
- Any silent stack/generation fallback is routed to an implementation child instead of being accepted without evidence.
