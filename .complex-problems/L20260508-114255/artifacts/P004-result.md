## Result: P004 Verification Guardrails And Docs Alignment Audit

### Done Items

- Inspected architecture docs and roadmap tickets related to generic FSM substrate, generic worker substrate, and business-only DSL migration.
- Inspected tests that guard generic FSM/worker substrate, registry wiring, physical residue, and handler lifecycle boundaries.
- Ran representative targeted tests.
- Compared docs against P001-P003 code findings.

### Protected Invariants

Current tests protect several important boundaries:

- Generic FSM substrate exists and is deterministic:
  - `tests/test_pr258_generic_fsm_substrate.py`
  - `tests/test_pr259_generic_fsm_store_outbox.py`
- Generic worker contracts and loops:
  - `tests/test_pr323_generic_worker_contracts.py`
  - `tests/test_pr324_generic_worker_loop.py`
  - `tests/test_pr332_concurrent_generic_worker.py`
- Worker registry / entrypoint residue:
  - `tests/test_pr335_worker_residue_guards.py`
  - `tests/test_pr337_worker_command_registry.py`
- Business handler thinness and lifecycle-free boundary:
  - `tests/test_pr338_business_handlers_lifecycle_free.py`
  - task/saga/health/scheduler handler cutover tests.

Representative verification passed:

```text
pytest -q tests/test_pr258_generic_fsm_substrate.py \
  tests/test_pr259_generic_fsm_store_outbox.py \
  tests/test_pr323_generic_worker_contracts.py \
  tests/test_pr324_generic_worker_loop.py \
  tests/test_pr332_concurrent_generic_worker.py \
  tests/test_pr335_worker_residue_guards.py \
  tests/test_pr337_worker_command_registry.py \
  tests/test_pr338_business_handlers_lifecycle_free.py

35 passed in 0.21s
```

```text
pytest -q tests/test_pr334_worker_process_runner.py \
  tests/test_pr335_worker_residue_guards.py \
  tests/test_pr337_worker_command_registry.py \
  tests/test_pr339_worker_startup_db_retry.py

14 passed in 0.11s
```

### Docs Alignment

The main architecture documents are mostly aligned:

- `docs/architecture/generic-fsm-substrate.md:1-18` records the harness FSM principles, including explicit boundaries and "stale branches are expensive".
- `docs/architecture/generic-fsm-substrate.md:21-44` defines the minimal state/event/decision/effect and durable outbox model.
- `docs/architecture/queue-service-durable-fsm-host-plan.md:84-93` states the completed task/saga/session/lease FSM and durable outbox shape.
- `docs/architecture/generic-worker-substrate-plan.md:35-67` records the generic employee / component lifecycle boundary and explicit dependency constraints.
- `docs/architecture/generic-worker-substrate-plan.md:100-117` marks phases 0-13 closed.

### Docs Residue / Ambiguity

There is a meaningful documentation mismatch:

- `docs/roadmap/tickets/PR-338-business-only-dsl-phase-bill.md:3` still says `Status: Doing`.
- The same file says `P007 in progress` at line 30, while `docs/architecture/generic-worker-substrate-plan.md:117` and `409-423` describe phase 13 / final DSL residue closure as closed.

That is exactly the kind of stale ledger residue that can mislead future agents.

There is also a target-language ambiguity:

- `generic-worker-substrate-plan.md:37-43` says business code should define explicit FSM states/events/decisions, typed job/result contracts, and tiny handler DSL adapters.
- `generic-worker-substrate-plan.md:90-97` still lists action engines as part of the target shape.
- Current code matches that documented target, but it does not match the stricter interpretation "business code is only declarative effect DSL and engines only emit explicit effects".

### Missing Guardrails

Current guardrails are strong against old lifecycle loops and retired entrypoints, but weak for the next ideal:

- No test enforces action engines to produce pure `Decision/EffectPlan` objects instead of directly calling clients.
- No guard caps or structurally validates the size/role of `worker_assemblies.py`; it is allowed to remain a thick imperative composition root.
- No deploy check appears to be timestamp-aware enough to distinguish fresh log failures from stale append-only log residue.
- No guard asserts process supervision/restart semantics, because current start scripts use background subprocesses.
- No docs lint catches stale roadmap ticket status such as PR-338 `Doing` after the architecture ledger says closed.

### Recommendation

The current verification is good for "generic worker substrate + thin handler boundary". It is not sufficient for the stricter "business only DSL / pure effect-plan engines / declarative assembly" ideal. The next optimization plan should add explicit tickets for:

1. Action engine decision/effect-plan model.
2. Assembly DSL shrink / structural guard for `worker_assemblies.py`.
3. Timestamp-aware deploy/log smoke checks.
4. Docs status consistency lint for active architecture ledgers and roadmap tickets.
5. Optional process supervision model if operational self-healing is part of the target.

### Artifacts

- `P004-ticket.md`
- This result file.
