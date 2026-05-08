# Check: Runtime Live Path Proof Accepted

## Result IDs

- R000

## Evidence

- Entrypoint evidence shows `scripts/start.sh` consumes `runtime_roster process-checks` and `runtime_roster launch-commands`.
- CLI evidence shows `main_novaic.py` delegates worker modes through `run_worker_mode_if_registered(...)`.
- Registry evidence shows `build_runtime_worker_registry()` returns `WorkerSpec` entries ordered by `RUNTIME_WORKER_MODES`.
- FSM evidence shows session/task/saga repositories record durable transitions through generic ledger repositories and `FsmTransitionRunner`.
- Verification commands passed:
  - `23 passed in 0.69s` for targeted FSM/roster/wiring tests.
  - `lint_runtime_worker_supervision OK`.
  - `lint_deploy_fresh_smoke OK`.

## Criteria Map

- Identify process launch entrypoints: satisfied by `scripts/start.sh` evidence.
- Prove roster/registry definitions are consumed: satisfied by `runtime_roster`, `main_novaic.py`, and `registry.py` evidence.
- Prove FSM infrastructure is referenced by live worker/queue code: satisfied by `session_repo.py`, `queue_db.py`, `saga_repo.py`, and `FsmTransitionRunner` evidence.
- Prove targeted CI/tests pass: satisfied by pytest and lint outputs.
- Label live-path gaps explicitly: satisfied by Known Gaps in R000, which defers pure DSL claims to P002.

## Execution Map

- Inspected launch scripts, worker registry, runtime roster, FSM runner, ledger repositories, and production wiring tests.
- Ran targeted tests and guard scripts without code changes.
- Recorded the result as R000.

## Stress Test

- Negative scenario considered: new runtime code could exist but production startup could still use old hard-coded worker commands. Evidence rejects this because `scripts/start.sh` uses `runtime_roster launch-commands` and the lint guard checks the same contract.
- Negative scenario considered: worker CLI could bypass registry. Evidence rejects this because `main_novaic.py` routes unknown worker modes through `run_worker_mode_if_registered`, and targeted registry tests passed.
- Negative scenario considered: FSM code could exist but repositories still write legacy tables directly. Evidence partially rejects this for transition recording because session/task/saga paths call ledger `record_transition`; DSL purity and remaining imperative business code are deferred to P002/P003.

## Residual Risk

- This check does not prove the runtime is pure DSL; it proves the new FSM/worker/roster path is live. Remaining purity and residue questions are intentionally represented by sibling problems P002 and P003.

## Decision

Success.
