# Result: Runtime Live Path Uses New FSM Worker Roster

## Summary

The current runtime launch path is wired through the new worker roster/registry and queue FSM infrastructure. This ticket proves the live path with static entrypoint tracing plus targeted tests and CI guards. This result does not claim the business layer is pure DSL; it only proves the new runtime/FSM path is connected and guarded.

## Done

- Traced `scripts/start.sh` to `runtime_roster launch-commands`, proving supervised runtime subprocess launch is sourced from the canonical roster instead of duplicated shell lists.
- Traced `main_novaic.py` to `run_worker_mode_if_registered()` and `build_runtime_worker_registry()`, proving worker CLI modes dispatch through the registry.
- Traced `task_queue/workers/registry.py` to `RUNTIME_WORKER_MODES` and `WorkerSpec` entries, proving the registry is ordered by the roster.
- Traced `queue_service/fsm/runner.py` and ledger repositories, proving session/task/saga durable transitions share `FsmTransitionRunner`.
- Ran targeted FSM/roster/production wiring tests and runtime supervision lints.

## Verification

- Static evidence:
  - `scripts/start.sh:60-62` defines `runtime_roster()` via `novaic-agent-runtime/scripts/runtime_worker_roster.py`.
  - `scripts/start.sh:109-114` verifies required process counts from `runtime_roster process-checks`.
  - `scripts/start.sh:259-260` launches worker processes from `runtime_roster launch-commands`.
  - `novaic-agent-runtime/main_novaic.py:126-145` builds the runtime worker registry and dispatches registered modes.
  - `novaic-agent-runtime/main_novaic.py:337-342` routes CLI worker modes through `run_worker_mode_if_registered(...)`.
  - `novaic-agent-runtime/task_queue/workers/runtime_roster.py:22-29` declares worker modes.
  - `novaic-agent-runtime/task_queue/workers/runtime_roster.py:32-133` declares supervised process roles and launch commands.
  - `novaic-agent-runtime/task_queue/workers/registry.py:26-110` builds `WorkerSpec` entries and returns them in `RUNTIME_WORKER_MODES` order.
  - `novaic-agent-runtime/queue_service/fsm/runner.py:50-93` is the generic durable transition write runner.
  - `novaic-agent-runtime/queue_service/session_ledger.py:69-73` constructs `FsmTransitionRunner`.
  - `novaic-agent-runtime/queue_service/session_repo.py:329-344` records dispatch transitions through `session_ledger.record_transition(...)`.
  - `novaic-agent-runtime/queue_service/queue_db.py:1300-1310` records task FSM transitions through `_task_ledger.record_transition(...)`.
  - `novaic-agent-runtime/queue_service/saga_repo.py:971-980` records saga FSM transitions through `_saga_ledger.record_transition(...)`.
- Test evidence:
  - `pytest -q tests/test_pr342_generic_fsm_transition_runner.py tests/test_pr343_runtime_worker_roster_ssot.py tests/test_pr260_session_harness_generic_fsm_cutover.py tests/test_pr306_taskqueue_fsm_cutover.py tests/test_pr310_saga_repository_fsm_cutover.py tests/test_pr337_worker_command_registry.py tests/test_pr302_session_outbox_worker_production_wiring.py`
  - Result: `23 passed in 0.69s`.
- Guard evidence:
  - `python3 scripts/ci/lint_runtime_worker_supervision.py` -> `lint_runtime_worker_supervision OK`.
  - `python3 scripts/ci/lint_deploy_fresh_smoke.py` -> `lint_deploy_fresh_smoke OK`.

## Known Gaps

- This ticket does not prove “pure DSL”. It proves the current runtime path is live-wired through the new roster/registry/FSM infrastructure.
- `worker_assemblies.py` is still hand-written Python assembly code; that belongs to the DSL purity gap audit.
- Action engines still need separate review to decide whether they are pure enough or should become plan-first DSL/policy tables.

## Artifacts

- `.complex-problems/L20260508-165336/artifacts/P001-ticket.md`
- Shell inspections over runtime entrypoints, worker roster, worker registry, FSM runner, and ledger repositories.
