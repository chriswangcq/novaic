# Runtime session authority cleanup result

## Summary

Completed the P407 bounded pass over runtime session-authority files. No new dangerous live session-generation compatibility residue was found. The remaining hits are explicit validators, read-only audit/projection helpers, start/no-active generation allocation, or non-session archive/retry metadata.

## Done

- Reran a correct array-based guard over session-authority files after catching an initial zsh variable-splitting false negative.
- Classified `session_repo.py` hits:
  - `_require_positive_generation` / `_require_non_negative_generation` are explicit validators.
  - `session_ended(...)` requires finalize generation, reason, and remaining stack before mutation.
  - attach path validates active session generation with `_require_positive_generation`.
  - runtime state adapters allow generation `0` only for `NO_ACTIVE`, not active session authority.
- Classified `session_fsm.py` hits:
  - `finalize_generation` is parsed by `_positive_generation_or_none`; invalid/missing values reject finalize.
  - accepted event generation equals explicit finalize generation.
  - non-negative validator is used for decision event generation metadata.
- Classified `session_ledger.py` hits:
  - generation parsing is an explicit non-negative validator.
  - `session_generation()` returns `1` for first active generation or `0` only when no active scope is requested; this is generation allocation, not missing finalize compatibility.
  - `record_active_session` writes explicit caller-provided generation.
- Classified `session_observed_events.py` hits:
  - wake-created observations require positive generation before recording active state.
- Classified `session_audit.py` and `queue_audit.py` hits:
  - read-only audit timeline/projection helpers; they do not clear, restart, or archive active sessions.
- Classified `session_outbox.py` and `session_recovery.py` hits:
  - remaining stack/finalize reason validation exists for archive/recovery payloads.
  - `round_num`, `max_retries`, and stack depth defaults are archive/retry metadata, not session-generation authority.

## Verification

- Guard artifact: `.complex-problems/L20260516-222011/tmp/p407/session-authority-guard.txt`.
- Focused runtime session-authority tests passed from `novaic-agent-runtime`:
  - `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr254_finalize_ownership.py tests/test_pr264_session_finalize_fsm_boundary.py tests/test_pr266_session_recovery_boundary.py tests/test_pr267_session_outbox_effect_boundary.py tests/test_pr235_session_ledger.py tests/test_pr295_session_audit_tooling.py tests/test_pr288_session_observed_event_handler.py`
  - Result: `40 passed in 0.38s`.

## Known Gaps

- None for P407's session-authority scope.
- Remaining generic Queue/task/worker hits are intentionally delegated to sibling children `P408`, `P409`, and `P410`.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p407/session-authority-guard.txt`
