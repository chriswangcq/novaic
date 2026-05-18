# Finalize/session-ended entry-point inventory result

## Summary

Completed the read-only finalize/session-ended entry-point inventory for P334. The live finalize boundary is centered on `wake_finalize -> session.ended -> SessionRepository.session_ended`, with additional producer/recovery paths from react sagas, saga compensation, suspected-dead recovery, recovery archive, and startup rebuild. One important risk was identified for downstream tickets: missing `session_generation` can become `generation=0`, and the finalize FSM currently treats zero as an implicit fallback to current generation.

## Entry-point map

### 1. Finalize producers from normal agent loop

- `task_queue/contracts/react_actions.py:271-344` decides whether actions should finalize.
  - Carries: `scope_id`, `round_num`, stack known/depth, force reason.
  - Delegated: safe-ish producer, but downstream must enforce generation.
- `task_queue/contracts/react_actions.py:388-411` builds `wake_finalize` trigger payload.
  - Carries: `scope_id`, `agent_root_scope_id`, `wake_scope_path`, `agent_id`, `subagent_id`, `user_id`, `session_generation`, `finalize_reason`, `round_num`, stack snapshot.
  - Classification: safe producer when `source.session_generation` is explicit.
- `task_queue/contracts/react_think.py:247-307` decides no-tool/round-cap finalize.
  - Carries decision reason and stack known/depth.
- `task_queue/contracts/react_think.py:357-382` builds `wake_finalize` trigger payload.
  - Carries same core fields as react_actions, including `session_generation`.
  - Classification: safe producer when context has explicit generation.

### 2. Wake finalize saga payload boundary

- `task_queue/sagas/wake_finalize.py:24-38` builds structural `cortex.scope_end` payload.
  - Carries: scope/root/path, agent/user, empty report, finalize reason, round.
  - Does not carry generation; it archives a named scope rather than active session state.
  - Delegated to P338/P339 for stale archive/recovery semantics.
- `task_queue/sagas/wake_finalize.py:67-68` computes session generation.
  - Risk: `int(ctx.get("session_generation") or 0)` converts missing generation to `0`.
  - This is unsafe when combined with repository finalize compatibility behavior.
  - Delegated to P336/P339.
- `task_queue/sagas/wake_finalize.py:71-84` builds remaining stack fallback.
  - Carries explicit `remaining_stack` if present, otherwise reconstructs from stack known/depth.
  - Delegated to P338 for reason/remaining-stack archive correctness.
- `task_queue/sagas/wake_finalize.py:87-98` builds `session.ended` payload.
  - Carries: agent/subagent/scope/root/path/finalize reason/generation/remaining stack/round.
  - Classification: live finalize payload boundary; missing-generation behavior needs downstream fix.
- `task_queue/sagas/wake_finalize.py:101-129` defines finalization step order:
  - `cortex_scope_end`
  - subagent lifecycle state
  - `session_ended`
  - Delegated to P337/P338 for stale handling/side-effect order checks.

### 3. Session-ended handler, HTTP boundary, and client

- `task_queue/handlers/session_handlers.py:14-63` handles `session.ended`.
  - Requires agent id, subagent id, scope id, finalize reason, generation not `None`, remaining stack dict.
  - Forwards generation to `saga_client.session_ended`.
  - Risk: `generation=0` is accepted because only `None` is rejected.
  - Delegated to P337/P339.
- `task_queue/client.py:468-491` posts `/api/queue/session-ended`.
  - Carries explicit generation and remaining stack.
  - Classification: transport boundary; safe if caller payload is safe.
- `queue_service/routes.py:543-549` defines `SessionEndedRequest`.
  - Requires `generation: int`, but does not constrain positive generation.
  - Delegated to P337/P339 for strict validation.
- `queue_service/routes.py:583-594` forwards request to repository.
  - Classification: thin route, no mutation by itself.

### 4. Repository/FSM mutation boundary

- `queue_service/session_repo.py:462-640` owns session finalize/restart mutation.
  - Requires non-empty finalize reason, generation not `None`, remaining stack not `None`.
  - Uses global transaction.
  - Calls `decide_session_finalize(...)` before recording finalization.
  - On reject, records `session_finalize_rejected` and returns without clearing active.
  - On accept, records `session_finalized`, records pending projection, then either `session_closed` or `session_restart_pending`.
  - Delegated to P335 for atomicity and positive-generation enforcement.
- `queue_service/session_fsm.py:182-214` wraps the finalize reducer.
  - Carries state generation, active scope, event scope, finalize generation.
- `queue_service/session_fsm.py:274-339` rejects generation mismatch only when `finalize_generation > 0`; otherwise it accepts using current generation.
  - Risk: missing generation normalized to `0` can close current active session if scope matches.
  - Delegated to P335/P339.
- `queue_service/session_ledger.py:329-362` records rejected finalization.
  - Carries finalize metadata, event generation, result, reason.
- `queue_service/session_ledger.py:364-415` records finalized state.
  - Writes `session_finalized`, then `ENDING`, then `NO_ACTIVE` state for the same event generation.
  - Delegated to P335 for mutation-boundary verification.

### 5. Pending restart path after finalize

- `queue_service/session_projection.py:49-80` builds unconsumed input projection.
  - Carries input event ids, trigger type, user id, metadata.
- `queue_service/session_projection.py:83-103` shapes pending restart source.
- `queue_service/session_projection.py:106-129` builds restart saga context.
  - Carries new `session_generation` plus `finalize` metadata.
  - Delegated to P335/P339 to ensure stale finalize cannot start a restart for a newer session.
- `queue_service/session_repo.py:580-640` starts pending restart after accepted finalize.
  - Uses `next_generation(session_key)` for the restarted wake.
  - Delegated to P335 and P339.

### 6. Saga failure compensation and recovery

- `queue_service/saga_repo.py:1156-1191` handles saga failure cases.
  - Failed wake/react saga creates `wake_finalize` compensation.
  - Failed `wake_finalize` creates a suspected-dead event.
- `queue_service/saga_repo.py:1255-1293` builds wake_finalize compensation.
  - Carries `session_generation` only if original saga context had it.
  - Risk: if missing, downstream wake_finalize emits generation `0`.
  - Delegated to P336/P339.
- `queue_service/saga_repo.py:1295-1370` records suspected-dead event.
  - Carries failed scope/saga, reason, wake path, agent root, round, user.
  - Event generation is taken from current session state.
  - Does not directly mutate active state.
  - Delegated to P338/P339 for stale recovery archive semantics.
- `queue_service/session_recovery.py:19-52` converts suspected-dead event to recovery marker.
- `queue_service/session_recovery.py:55-96` builds recovered wake dispatch metadata.
- `queue_service/session_recovery.py:99-129` builds recovery archive outbox effect.
  - Carries failed scope/root/path/finalize reason/round, no session generation.
  - Delegated to P338/P339 because it archives a failed scope independently of active clearing.
- `queue_service/session_outbox.py:196-215` publishes recovery archive as `cortex.scope_end`.
  - Requires scope id, but no generation.
  - Delegated to P338/P339.

### 7. Cortex archive / skill-end lifecycle

- `task_queue/handlers/cortex_handlers.py:39-164` handles `cortex.scope_end`.
  - Snapshots input message ids, archives scope, transitions notifications processed, clears bridge cache.
  - Carries reason/round only; no generation check.
  - Delegated to P338 because stale archives must be scoped by explicit scope id and not active state.
- `task_queue/handlers/cortex_handlers.py:207-235` handles explicit `skill_end`.
  - Closes current child skill, not a session finalize by itself.
  - Relevant because remaining stack depth decides whether later finalize occurs.
  - Delegated only for stack/reason archive semantics if needed.

### 8. Startup rebuild / recovery-like projection

- `queue_service/session_rebuild.py:11-44` rebuilds session_state from running sagas on startup.
  - First marks active states `NO_ACTIVE`, then records running saga contexts.
  - Risk: `generation=int(context.get("session_generation") or 1)` falls back to generation `1`.
  - This is already aligned with sibling P329 missing/stale generation compatibility residue guard audit.

## Existing coverage map

- `tests/test_pr254_finalize_ownership.py`
  - explicit finalize contract required
  - persisted reason/generation/stack
  - generation mismatch rejection
  - scope mismatch rejection
  - wake_finalize payload carries contract
  - handler requires/forwards finalize contract
- `tests/test_pr264_session_finalize_fsm_boundary.py`
  - pure finalize FSM accept/reject behavior.
- `tests/test_pr270_session_finalize_ledger_boundary.py`
  - ledger-owned finalized/rejected event facts.
- `tests/test_pr243_inbox_restart_cutover.py`, `tests/test_pr241_pending_inbox_projection.py`, `tests/test_pr251_wake_creation_outbox_cutover.py`
  - pending restart behavior after session_ended.
- `tests/test_pr245_suspected_dead_recovery.py`, `tests/test_pr233_active_inbox_dispatch.py`, `tests/test_pr247_recovery_outbox_cutover.py`, `tests/test_pr266_session_recovery_boundary.py`
  - wake_finalize failure and recovery archive behavior.
- `tests/test_scope_end_environment_notifications.py`, `tests/test_pr70_explicit_skill_summary_only.py`
  - Cortex scope_end archive/notification behavior.

## Downstream targets

- P335 should fix/verify repository and FSM positive-generation behavior so `0` cannot act as "current generation" for finalize.
- P336/P337 should verify session-ended/outbox/handler payload validation rejects missing or zero generation before repository mutation.
- P338 should verify recovery archive and remaining-stack/reason records are tied to explicit failed scope, not current active session lookup.
- P339 should run aggregate source guards including `session_generation.*or 0`, `finalize_generation.*or current_generation`, and rebuild `or 1` compatibility residue.

## Verification

Read-only inventory commands used:

```bash
rg -n "finaliz|session_ended|session-ended|session\\.ended|ended|end_session|session end|watchdog|recovery|recover|restart|remaining_stack|remaining stack|skill_end|scope_end|archive|archiv" queue_service task_queue tests -g '*.py'
rg -n "SessionEventType|SessionOutboxEffect|build_.*effect|session\\.(attach_input|ended|start|recover)|finalize|restart" queue_service task_queue tests -g '*.py'
rg -n "def .*session|def .*final|def .*end|handle_.*session|handle_.*end|recover|watchdog|restart" queue_service task_queue -g '*.py'
rg -n "mark_active_states_no_active|record_session_finalized\\(|record_session_finalize_rejected\\(|session_generation\\(|next_generation\\(|generation is required|finalize_generation|session_generation" queue_service task_queue tests -g '*.py'
rg -n "session\\.ended|session_ended|SESSION_ENDED|CORTEX_SCOPE_END|scope_end|build_recovery_archive_effect|RECOVERY_ARCHIVE_SCOPE|create_wake_finalize_saga|record_session_suspected_dead" queue_service task_queue tests -g '*.py'
```

No implementation files were changed by this inventory ticket.
