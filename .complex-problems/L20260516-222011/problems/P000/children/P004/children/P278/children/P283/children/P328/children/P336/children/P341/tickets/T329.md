# Wake-finalize payload positive generation

## Problem Definition

`task_queue/sagas/wake_finalize.py` currently builds `session.ended` payloads using `_session_generation(ctx) -> int(ctx.get("session_generation") or 0)`. That fallback can emit a malformed finalize delivery payload with `generation=0`, pushing ambiguity downstream. Wake-finalize must fail closed instead of publishing a zero-generation session-ended effect.

## Proposed Solution

1. Replace `_session_generation(ctx)` with strict extraction that requires `session_generation` to be present and positive.
2. Make `_build_session_ended_payload(ctx)` call the strict extractor and preserve the existing `finalize_reason` and `remaining_stack` behavior.
3. Add tests in `tests/test_pr254_finalize_ownership.py` or a focused test file proving:
   - positive session generation is preserved in the payload.
   - missing `session_generation` raises.
   - zero `session_generation` raises.
4. Run focused finalize tests and a source guard proving `wake_finalize.py` no longer contains `session_generation") or 0`.

## Acceptance Criteria

- `wake_finalize.py` no longer silently emits `generation=0`.
- Missing or non-positive session generation fails before the `session.ended` payload is published.
- Existing valid wake-finalize payload test still passes.
- New tests cover missing and zero generation.

## Verification Plan

- `python3 -m py_compile task_queue/sagas/wake_finalize.py`
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr254_finalize_ownership.py`
- Source guard: `! rg -n 'session_generation\"\\) or 0|session_generation.*or 0' task_queue/sagas/wake_finalize.py`

## Risks

- If upstream still creates wake-finalize contexts without generation, these contexts will now fail earlier. That is intended, but P337/P339 must handle upstream contract cleanup if tests expose it.

## Assumptions

- Wake-finalize should not compensate for missing generation; it should reject malformed context and let recovery/watchdog handle the failed saga path.
