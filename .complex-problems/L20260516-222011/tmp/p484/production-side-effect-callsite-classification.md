# Production side-effect callsite classification

## Raw Query

- Raw artifact: `.complex-problems/L20260516-222011/tmp/p484/production-side-effect-callsite-raw.txt`
- Raw line count: `73`

## Classification Table

| File / call site | Category | Rationale | Route |
|---|---|---|---|
| `queue_service/main.py` `SagaOrchestrator(...)` | service assembly boundary | Queue service creates the orchestrator dependency once and passes it into routes/outbox components. | Retain |
| `task_queue/workers/assembly_factories.py` `SagaOrchestrator(...)` | worker assembly boundary | Session/saga outbox worker process specs assemble the orchestrator dependency for worker handlers. | Retain |
| `queue_service/routes.py` `SagaOrchestrator(...)` | route factory fallback assembly | Factory can create an orchestrator when not injected. This is not a session side-effect call by itself, but overlaps with assembly responsibility. | P485 should decide whether to retain/tighten |
| `queue_service/routes.py:219` `queue.publish(...)` | generic task queue adapter API | Public/internal task publish route directly creates tasks. It is generic queue infrastructure, not session-owned effect dispatch, but it is the most visible direct publish API. | P485 |
| `queue_service/session_outbox.py:185` `self.saga_orchestrator.create(...)` | durable session outbox dispatcher boundary | Session-owned wake saga creation leaves the durable session outbox here. | P486 guard/harden |
| `queue_service/session_outbox.py:212` `self.queue.publish(...)` | durable session outbox dispatcher boundary | Recovery archive effect leaves the durable session outbox here. | P486 guard/harden |
| `queue_service/session_outbox.py:255` `self.queue.publish(...)` | durable session outbox dispatcher boundary | Attach input effect leaves the durable session outbox here. | P486 guard/harden |
| `queue_service/session_repo.py:451-455` recovery archive effect | session-owned outbox effect writer | Repository records an outbox effect; it does not publish directly. | Retain |
| `queue_service/session_repo.py:929-930` attach input effect | session-owned outbox effect writer | Repository records an outbox effect; it does not publish directly. | Retain |
| `queue_service/session_wake_plan.py:76/113` create wake saga effect | session-owned outbox effect builder | Wake plan builds durable outbox payloads. | Retain |
| `task_queue/workers/saga_effects.py:35` `task_client.publish(...)` | generic worker effect executor | Saga FSM emits an effect, this executor performs generic task publish. | Retain |
| `task_queue/workers/task_effects.py:84` `client.publish(...)` | generic worker effect executor | Task worker FSM emits an effect, this executor performs generic task publish. | Retain |
| `queue_service/queue_db.py` and `task_queue/client.py` examples | docs/example guard | Example snippets in docstrings/readme-style code, not live session bypasses. | Retain/no action |
| `queue_service/saga_repo.py` compensation/session suspected dead effect builders | saga-owned outbox/effect logic | Saga repository builds explicit compensation/recovery effects, not raw session dispatch. | Retain |

## Suspicious / Ambiguous

- No high-confidence stale production side-effect bypass was found in this classification pass.
- `queue_service/routes.py:219` remains ambiguous enough to require P485's explicit boundary decision.
- `session_outbox.py` direct effects are expected, but P486 should harden guard coverage because this is the sanctioned side-effect outlet.

## Production Source Change Check

- `git-status-before.txt` and `git-status-after.txt` match except for the header line. This classification child did not change production source.
