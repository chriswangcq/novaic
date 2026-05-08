## Result: P000 Full Audit Of Current FSM Substrate And Business DSL Gap

### Executive Finding

The current system is genuinely on the new architecture path. It is not a fake cutover where old worker files still run. The generic FSM substrate, generic worker substrate, unified runtime registry, and thin business handler DSL are present and tested.

However, it is not yet the strict "business code is only a few lines of declarative DSL" ideal. The real remaining gap is one layer deeper: action engines and assembly code are still imperative protocol/effect orchestration. They are explicit and tested, but not yet pure decision/effect-plan DSLs with small infrastructure adapters.

### Current Achieved Shape

1. Generic FSM substrate:
   - `queue_service/fsm/core.py` defines pure state/event/decision/reducer primitives.
   - `queue_service/fsm/sqlite_store.py` provides a business-agnostic SQLite-backed store/outbox substrate.

2. Generic worker substrate:
   - `queue_service/worker/contracts.py` defines generic job/result/source/handler/reporter contracts.
   - `queue_service/worker/generic_worker.py` and `concurrent_worker.py` own lifecycle, polling, handler execution, reporting, metrics, sleep, shutdown, and error isolation.

3. Business handler DSL:
   - `task_worker.py`, `saga_worker.py`, `health_worker.py`, and `scheduler_worker.py` are small typed job-boundary handlers.
   - They declare `WorkerJobSpec`, decode `WorkerJob`, delegate to injected engines, and return `WorkerResult`.
   - They do not construct worker loops, clients, runtime dependencies, or process entrypoints.

4. Runtime wiring:
   - Retired `main_task.py` and `main_saga.py` are physically absent.
   - Worker modes are registered through `task_queue/workers/registry.py`.
   - Startup scripts and deployed processes use `main_novaic.py task-worker/saga-worker/session-outbox-worker/saga-outbox-worker/health/scheduler`.
   - Deployment evidence showed 10 worker processes and no live old worker path.

5. Verification:
   - Targeted FSM/worker/registry/residue/business-handler tests passed.
   - Current tests catch many old-path regressions.

### Gap Against The "Perfect" Shape

The perfect target would be:

```text
business DSL:
  declarative job/event spec
  pure decision function
  explicit effect plan

component substrate:
  worker loop
  leases/concurrency/backoff
  durable outbox
  effect adapters
  process supervision
```

Current gap:

1. Action engines are still imperative:
   - `TaskExecutionEngine` directly performs heartbeat, idempotency, task complete/fail, retry, saga parallel publish, and polling.
   - `SagaLaunchEngine` directly publishes DAG tasks and marks saga state.
   - `HealthRecoveryEngine` directly owns an HTTP client and calls recovery APIs.
   - `ScheduledWakeEngine` directly scans due agents and dispatches wake through assembler.

2. Assembly is still thick:
   - `worker_assemblies.py` is a 652-line composition root with DB retry, client construction, metrics startup, engine construction, source construction, and worker construction.
   - This is acceptable as a composition root, but not the final compact assembly DSL.

3. Guardrails are current-shape, not perfect-shape:
   - Existing tests protect old worker loop deletion and handler thinness.
   - They do not enforce action engines returning pure effect plans.
   - They do not structurally cap or validate assembly thickness.

4. Operational evidence has residue risk:
   - Deployment uses visible shell-spawned subprocesses, not a stronger process supervisor.
   - Append-only logs can contain stale historical errors and mislead future audits unless checks are timestamp-aware.

5. Documentation has one stale status mismatch:
   - `docs/roadmap/tickets/PR-338-business-only-dsl-phase-bill.md` still says `Status: Doing` and `P007 in progress`.
   - `docs/architecture/generic-worker-substrate-plan.md` says the relevant phases are closed.

### Verification Performed

- P001: generic FSM/worker substrate boundary audit.
- P002: business handler/action-engine DSL gap audit.
- P003: runtime wiring, deployment process, and old-path residue audit.
- P004: verification guardrail and docs alignment audit.

Targeted tests run:

```text
22 passed - business handler lifecycle/cutover tests
35 passed - FSM/worker substrate, registry, residue, business boundary tests
14 passed - process runner, registry, startup DB retry, residue tests
```

Deployment/runtime evidence:

- `./deploy status` reported all core backend ports up and 10 workers.
- Remote `ps` showed queue-service, task-worker x4, saga-worker x2, session-outbox-worker, saga-outbox-worker, health, scheduler, and subscriber.

### Recommended Next Optimization Tickets

1. **Action Engine Effect-Plan DSL**
   - Convert task/saga/health/scheduler engines from direct side-effect execution to `Decision + EffectPlan`.
   - Keep effect adapters in infrastructure.

2. **Assembly DSL Shrink**
   - Replace large imperative `worker_assemblies.py` factories with declarative assembly specs.
   - Move DB startup retry and metrics-server startup into reusable component policies.

3. **Effect Adapter Guardrails**
   - Add tests proving business engines do not directly call protocol clients except through approved effect adapters.

4. **Docs Status Consistency Lint**
   - Fail if architecture phase ledger says closed while roadmap ticket says doing/in progress.

5. **Timestamp-Aware Deploy Smoke**
   - Check worker health from fresh timestamps or structured status endpoints, not raw tail of append-only logs.

6. **Optional Process Supervisor**
   - If runtime self-healing is a target, replace shell backgrounding with supervisor/systemd-style worker units or explicit monitor.

### Artifacts

- `.complex-problems/L20260508-114255/artifacts/P001-result.md`
- `.complex-problems/L20260508-114255/artifacts/P002-result.md`
- `.complex-problems/L20260508-114255/artifacts/P003-result.md`
- `.complex-problems/L20260508-114255/artifacts/P004-result.md`
- This result file.
