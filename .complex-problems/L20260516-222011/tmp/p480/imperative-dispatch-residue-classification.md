# Imperative dispatch residue classification

## Raw Guard Summary

- Raw guard artifact: `.complex-problems/L20260516-222011/tmp/p480/imperative-dispatch-residue-raw-guards.txt`
- Total raw lines: `1078`
- Direct saga creation / saga orchestration hits: `132`
- Direct queue publish / side-effect publish hits: `125`
- Active session / session mutation vocabulary hits: `159`
- Finalize / session-ended / generation compatibility vocabulary hits: `658`

## Required Boundary

- `novaic-agent-runtime/queue_service/main.py` and `novaic-agent-runtime/task_queue/workers/assembly_factories.py` construct `SagaOrchestrator` at service/worker assembly boundaries.
- `novaic-agent-runtime/task_queue/handlers/saga_handlers.py`, `task_queue/topics.py`, and saga definitions use `SagaTopics` as the normal saga execution substrate.
- `novaic-agent-runtime/queue_service/session_outbox.py` is the expected session outbox dispatcher boundary. Its direct `saga_orchestrator.create` and `queue.publish` calls are downstream of durable outbox rows.
- `novaic-agent-runtime/queue_service/session_repo.py` writes session outbox effects (`RECOVERY_ARCHIVE_SCOPE`, `PUBLISH_ATTACH_INPUT`) rather than directly publishing side effects.
- `novaic-agent-runtime/task_queue/workers/saga_effects.py` and `task_queue/workers/task_effects.py` are generic worker effect executor boundaries.
- `novaic-agent-runtime/queue_service/session_fsm.py` contains explicit `missing_generation` decision reasons; this is FSM validation language, not a fallback compatibility path.

## Test / Docs Guard

- Most `SagaOrchestrator` and outbox effect string hits in `novaic-agent-runtime/tests/` are construction fixtures or guard assertions.
- Old effect strings such as `observe_create_wake_saga` appear in tests that verify the old effect is no longer written by current dispatch paths.
- `tq_active_sessions`, `legacy`, `compat`, and `fallback` test hits are mostly regression guards that assert retired compatibility paths stay removed.
- `queue_service/queue_db.py` and `task_queue/client.py` examples show generic task queue usage, not session harness direct side-effect bypasses.

## High-Confidence Removable Residue

- None identified at inventory confidence. The scan did not surface an obvious production branch that can be safely deleted without the focused cleanup children.

## Ambiguous / Downstream Cleanup Candidates

- `novaic-agent-runtime/queue_service/routes.py:219` exposes a generic `/tasks/publish` direct `queue.publish` API. It may be a required internal queue adapter, but P481 should classify it against the FSM/outbox direction.
- `novaic-agent-runtime/queue_service/session_outbox.py` direct side effects are currently classified as required outbox dispatcher boundaries, but P481 should keep their narrow guard coverage because they are the only production place where session outbox effects leave the durable ledger.
- Finalize/session-ended vocabulary is broad and mostly active runtime behavior; P482 should inspect representative finalize/session-ended branches so no stale compatibility path is hidden by generic wording.

## Production Source Change Check

- `git-status-before.txt` and `git-status-after.txt` match except for the header line. No production source delta was introduced by this inventory child.
