# Session-ended delivery chain inventory result

## Summary

Mapped the live session-ended/finalize delivery chain. The chain is mostly explicit, but three unsafe or incomplete boundaries remain: `wake_finalize` still converts missing `session_generation` to `0`, `handle_session_ended` only checks generation presence and then casts with `int(...)`, and `SessionEndedRequest` declares `generation: int` without positivity validation. Broader react contract defaults also still produce `session_generation=0`, but those are upstream of the delivery-boundary fix and should remain delegated to P337/P339 unless required by P336 checks.

## Done

- Identified the live delivery chain:
  - `novaic-agent-runtime/task_queue/sagas/wake_finalize.py::_build_session_ended_payload`
  - `novaic-agent-runtime/task_queue/handlers/session_handlers.py::handle_session_ended`
  - `novaic-agent-runtime/task_queue/client.py::TaskQueueClient.session_ended`
  - `novaic-agent-runtime/queue_service/routes.py::SessionEndedRequest` and `/session-ended` route
  - `novaic-agent-runtime/queue_service/session_repo.py::SessionRepository.session_ended`
- Identified existing tests:
  - `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py::test_wake_finalize_payload_carries_finalize_contract`
  - `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py::test_session_ended_handler_requires_and_forwards_finalize_contract`
  - `novaic-agent-runtime/tests/test_pr255_legacy_compat_cleanup.py::test_finalize_contract_is_required_at_public_boundaries`
- Classified boundaries:
  - Safe enough after P335: repository rejects missing/non-positive generation and checks stale generation/scope in transaction.
  - Unsafe for P341: `wake_finalize.py::_session_generation(ctx)` returns `int(ctx.get("session_generation") or 0)`.
  - Unsafe for P342: handler rejects `generation is None` but allows `0`, negative, and string values that cast successfully.
  - Incomplete for P342: route schema uses plain `generation: int`, so API accepts zero/non-positive generation before repository rejection.
  - Delegated to P343/P337/P339: `react_think.py` and `react_actions.py` default `session_generation` to `0` in their context contracts.

## Verification

- Read live source with `nl -ba` for:
  - `task_queue/sagas/wake_finalize.py`
  - `task_queue/handlers/session_handlers.py`
  - `task_queue/client.py`
  - `queue_service/routes.py`
  - `task_queue/contracts/react_think.py`
  - `task_queue/contracts/react_actions.py`
- Ran targeted searches:
  - `rg -n "SessionEndedRequest|/api/queue/session-ended|session-ended|session_ended\\(" novaic-agent-runtime/tests novaic-agent-runtime/queue_service novaic-agent-runtime/task_queue -g '*.py'`
  - `rg -n "session_generation\\) or 0|session_generation" novaic-agent-runtime/task_queue/sagas/wake_finalize.py novaic-agent-runtime/task_queue/contracts/react_think.py novaic-agent-runtime/task_queue/contracts/react_actions.py novaic-agent-runtime/tests -g '*.py'`

## Known Gaps

- P341 should remove/replace `wake_finalize.py::_session_generation(ctx)` fallback and add payload-builder negative tests.
- P342 should harden `handle_session_ended`, `TaskQueueClient.session_ended` as needed, and `SessionEndedRequest` with positive generation validation.
- P343 should remove or explicitly delegate remaining compatibility/source residue, including tests that assert `session_generation=0` outside the P336 delivery path.
- P344 should run aggregate verification and ensure old paths are not still active.

## Artifacts

- `novaic-agent-runtime/task_queue/sagas/wake_finalize.py`
- `novaic-agent-runtime/task_queue/handlers/session_handlers.py`
- `novaic-agent-runtime/task_queue/client.py`
- `novaic-agent-runtime/queue_service/routes.py`
- `novaic-agent-runtime/task_queue/contracts/react_think.py`
- `novaic-agent-runtime/task_queue/contracts/react_actions.py`
- `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py`
- `novaic-agent-runtime/tests/test_pr255_legacy_compat_cleanup.py`
