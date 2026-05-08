# Repair dispatch, saga claim, deploy, and smoke test

## Problem Definition

Production user messages can persist in Entangled but fail to reach the queue/session runtime. The observed failure combines short Business subscriber dispatch timeout, Queue Service global lock contention, and saga claim 500s caused by SQLite database locks while writing FSM events.

## Proposed Solution

Fix the full runtime handoff path in small verifiable steps:

1. Inspect the exact dispatch, session repository, saga repository, FSM SQLite store, and worker claim-polling code.
2. Patch the immediate dispatch timeout so subscriber calls use the configured service timeout instead of httpx's default 5s.
3. Patch the durable FSM SQLite store / transaction boundaries so saga claim event writes do not raise `database is locked` during normal concurrent worker polling.
4. Add focused tests that reproduce the timeout/config and saga claim/database-lock path.
5. Run local tests.
6. Deploy to production.
7. Run production smoke checks proving a new IM reaches queue/session runtime activity.

## Acceptance Criteria

- The identified code paths are patched rather than bypassed.
- Tests fail on the prior behavior or directly guard the production regression.
- Production services are redeployed.
- Production logs/DBs show a new test input no longer fails at notification dispatch and does reach queue/session state.
- Any remaining runtime blockage is captured as a follow-up with concrete evidence.

## Verification Plan

- Run targeted unit tests for `novaic-common` and `novaic-agent-runtime`.
- Run any available smoke/deploy validation script after deployment.
- Query production `entangled.db` and `queue.db`.
- Tail production subscriber, queue-service, saga-worker, and task-worker logs around the smoke input.

## Risks

- Full conversational reply may still depend on provider/LLM availability; smoke must at minimum prove message handoff and runtime activity.
- SQLite contention can have multiple contributing paths; if one patch does not close it, create follow-up tickets instead of declaring success.
- Production contains stale pending saga/outbox rows; repair may need a small recovery step after code deployment.

## Assumptions

- The deployment target remains `root@api.gradievo.com`.
- It is acceptable to modify runtime/common code, deploy, and run a controlled smoke input.
