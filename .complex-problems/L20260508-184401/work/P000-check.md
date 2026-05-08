# Check root dispatch repair

## Evidence

- Result `R003` summarizes successful child work and production smoke.
- P001/P002/P003 are checked successful.
- Production smoke notification `18c14d716c0a` created Entangled records,
  produced exactly one Queue `input_received`, produced exactly one
  `dispatch_wake_start_queued`, created wake scope
  `2c4fbe39-8ff6-4b8e-b5c8-3bd13e0690d0`, and executed Runtime tasks through
  `im_read` and `llm.call`.
- After the dispatch TTL, the notification remained at `dispatch_attempts=1`
  with `dispatch_claim_id=delivered:subscriber`, so the duplicate redelivery
  failure mode did not recur.

## Criteria Map

- Remove normal `database is locked` dispatch/claim failure: satisfied by code
  repair and targeted regression tests around short background budgets,
  scoped busy timeout, and standalone FSM store commits.
- Business subscriber timeout explicit: satisfied by the configured sync HTTP
  timeout test and deployed `DispatchAssembler` sync client change.
- Queue dispatch / saga claim tests: satisfied by runtime targeted tests.
- Production deployed: satisfied by `./deploy services` and fresh-smoke.
- Real IM smoke shows queue/runtime activity: satisfied by the live
  `18c14d716c0a` evidence.
- Remaining risks recorded: satisfied by R003 and this check.

## Execution Map

- Implemented code in common, runtime queue service, and business subscriber /
  environment repository.
- Ran local targeted tests for business/common/runtime.
- Deployed all backend services.
- Queried production Entangled and Queue SQLite ledgers after live smoke and
  after TTL.

## Stress Test

The smoke waited beyond the prior `claim_ttl_ms` duplicate window. If the old
no-op dispatch success path were still active, the notification would have
been redispatched and `dispatch_attempts` / `input_received` would have
increased. They stayed at one.

## Residual Risk

No remaining root-harness dispatch gap is known. Full natural-language reply
quality and timing still depend on the LLM/provider and agent behavior above
the harness; that is outside this state-machine/dispatch repair.
