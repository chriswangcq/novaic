# P514 Static Residue Guard Design

## Scope

- Production runtime paths: `novaic-agent-runtime/queue_service`, `novaic-agent-runtime/task_queue`, `novaic-agent-runtime/queue_service/fsm`.
- Test paths: `novaic-agent-runtime/tests` only for expected regression coverage classification.
- Excluded: docs and ledger artifacts are not production residue.

## Guard Terms

- Active pointer remnants: `active_sessions`, `tq_active_sessions`, `active_session`, `legacy_active`.
- Direct side effects bypassing durable outbox/FSM: `SagaOrchestrator.create`, `.create_saga(`, `publish(`, `enqueue_task(`, `insert into tq_tasks`, `insert into tq_sagas`.
- Imperative session branching remnants: `if .*no_active`, `if .*active`, `suspected_dead`, `recovering`, `SessionDecision`, `remaining_stack`.
- Compatibility/backward paths: `deprecated`, `compat`, `legacy`, `fallback`, `best_effort`, `optional`.

## Proposed Scan Command

```bash
PATTERN='active_sessions|tq_active_sessions|active_session|legacy_active|SagaOrchestrator\.create|create_saga\(|publish\(|enqueue_task\(|insert into tq_tasks|insert into tq_sagas|if .*no_active|if .*active|suspected_dead|recovering|SessionDecision|remaining_stack|deprecated|compat|legacy|fallback|best_effort|optional'
rg -n --hidden -S "$PATTERN" novaic-agent-runtime/queue_service novaic-agent-runtime/task_queue novaic-agent-runtime/queue_service/fsm novaic-agent-runtime/tests
```

## Pattern Artifact

- `.complex-problems/L20260516-222011/tmp/p514/guard-pattern.txt`
- `.complex-problems/L20260516-222011/tmp/p514/guard-terms.txt`

## Expected Classification Categories

- Live expected path: current FSM/session/outbox/finalize code that must retain the vocabulary.
- Regression test: tests intentionally asserting old residue is gone or current boundary holds.
- Documentation/comment: non-executable explanation; cleanup if stale/misleading.
- Risky residue: production path bypasses FSM/outbox/session repository ownership or keeps compatibility fallback.

## P512 Requirements

- Run the proposed scan and save raw output/counts.
- Classify every production hit category.
- If any risky residue remains, create a follow-up instead of marking success.
