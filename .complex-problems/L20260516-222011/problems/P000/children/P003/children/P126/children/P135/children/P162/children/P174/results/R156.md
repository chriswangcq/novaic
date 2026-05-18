# Runtime wake continuity residue classified

## Summary

Classified runtime wake/session continuity residue. `session.init` is active-safe: it creates the agent root and wake child scopes, writes only current explicit inputs, and registers current notification ids. `session.attach_input` is active-safe: it is generation/wake checked before appending ids to an active wake. Old wake replay producers are absent. One cwd-dependent test was fixed during verification.

## Done

- Mapped `session.init` at `novaic-agent-runtime/task_queue/handlers/runtime_handlers.py:29`.
- Classified cross-wake continuity comments/behavior at `runtime_handlers.py:18-26`, `:101-120`, and `:152-154`: continuity is assembled by Cortex ContextEvents/folded summaries, not synthesized by runtime.
- Mapped agent-root/wake child creation and meta updates at `runtime_handlers.py:70-99`.
- Mapped current-turn input registration at `runtime_handlers.py:170-195`.
- Mapped `session.attach_input` at `runtime_handlers.py:226-305`.
- Classified `session.attach_input` as active-safe because it requires `expected_wake_scope_id` and `expected_session_generation`, verifies current root meta, and only then appends input ids.
- Fixed `novaic-agent-runtime/tests/test_pr266_session_recovery_boundary.py` to read source files relative to the test file rather than current working directory.

## Verification

- Initial focused run exposed a cwd-dependent static test failure in `test_pr266_session_recovery_boundary.py`.
- After the test fix:
  `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/test_pr113_no_wake_im_replay.py novaic-agent-runtime/tests/test_pr238_generation_checked_attach.py novaic-agent-runtime/tests/test_pr233_active_inbox_dispatch.py novaic-agent-runtime/tests/test_pr67_wake_child_scope.py novaic-agent-runtime/tests/test_pr70_explicit_skill_summary_only.py novaic-agent-runtime/tests/test_pr266_session_recovery_boundary.py novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py`
- Result: `35 passed in 0.20s`.

## Known Gaps

- Broader `read_context` caller inventory remains sibling `P175`.

## Artifacts

- Modified `novaic-agent-runtime/tests/test_pr266_session_recovery_boundary.py`.
