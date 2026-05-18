# Upstream react generation default classification result

## Summary

Upstream `react_think` and `react_actions` still default missing `session_generation` to `0`, and their finalize-trigger payload builders forward that value into `wake_finalize` context. This is not acceptable as final architecture, but it is not a blocker for P336 session-ended delivery correctness after P341/P342 because zero generation now fails closed before a `session.ended` payload is accepted or delivered. The upstream defaults should be removed under P337/P339 rather than hidden as P336 delivery cleanup.

## Done

- Inspected `novaic-agent-runtime/task_queue/contracts/react_think.py`:
  - `ReactThinkInput.session_generation: int = 0`
  - `from_context(...)` uses `int(ctx.get("session_generation") or 0)`
  - `build_trigger_finalize(...)` forwards `source.session_generation` into `wake_finalize` context.
- Inspected `novaic-agent-runtime/task_queue/contracts/react_actions.py`:
  - `ReactActionsInput.session_generation: int = 0`
  - `from_context(...)` uses `int(ctx.get("session_generation") or 0)`
  - `build_trigger_finalize_payload(...)` forwards `source.session_generation` into `wake_finalize` context.
- Verified P336 fail-closed guards:
  - `wake_finalize.py` no longer has `session_generation or 0`.
  - `session_handlers.py` no longer has presence-only `if generation is None` validation.
  - `routes.py` no longer has plain `generation: int` for `SessionEndedRequest`.

## Verification

- Read `react_think.py`, `react_actions.py`, and direct P336 delivery guards with `nl`/`rg`.
- Ran direct guard commands:
  - `! rg -n 'session_generation"\\) or 0|session_generation.*or 0' task_queue/sagas/wake_finalize.py`
  - `! rg -n 'if generation is None' task_queue/handlers/session_handlers.py`
  - `! rg -n 'generation:\\s*int\\s*$' queue_service/routes.py`

## Known Gaps

- Upstream react contract defaults remain real residue. They should be removed in the broader finalize/runtime contract work (P337/P339) because they can create failed wake-finalize sagas if a context is missing generation.
- For P336 specifically, the bad upstream value no longer becomes an accepted malformed `session.ended` delivery effect.

## Artifacts

- `novaic-agent-runtime/task_queue/contracts/react_think.py`
- `novaic-agent-runtime/task_queue/contracts/react_actions.py`
- P341/P342 delivery guard evidence.
