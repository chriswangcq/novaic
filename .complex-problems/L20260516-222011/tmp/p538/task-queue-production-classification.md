# P538 Task Queue Production Residue Classification

## Source

- Input: `.complex-problems/L20260516-222011/tmp/p531/static-residue-production.txt`
- Filtered hits: `.complex-problems/L20260516-222011/tmp/p538/task-queue-production-hits.txt`
- Counts: `.complex-problems/L20260516-222011/tmp/p538/task-queue-production-counts.txt`
- Context slices: `.complex-problems/L20260516-222011/tmp/p538/task-queue-production-context.txt`

## Totals

- Total task_queue production hits: 45
- Unique task_queue production files: 14

## Classification Table

| File | Hits | Matched Surface | Category | Rationale | Follow-up |
| --- | ---: | --- | --- | --- | --- |
| `novaic-agent-runtime/task_queue/client.py` | 4 | `publish`, `remaining_stack` | Live expected API/client surface | `publish()` is the current TaskQueue client boundary used by worker effect interpreters; `session_ended()` carries the explicit finalize contract with `generation` and `remaining_stack`. | No |
| `novaic-agent-runtime/task_queue/contracts/react_actions.py` | 2 | `remaining_stack` | Live expected FSM action contract | ReactActions builds `wake_finalize` saga context from a decision and includes a structured stack snapshot so finalize is explicit and auditable. | No |
| `novaic-agent-runtime/task_queue/contracts/react_think.py` | 1 | `remaining_stack` | Live expected FSM decision contract | ReactThink emits the same finalize payload contract when the model has no further tool calls and must close the wake. | No |
| `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py` | 4 | `remaining_stack` | Live expected handler validation | `cortex.scope_end` now requires a dict `remaining_stack` and passes it to Cortex archive; this is not compatibility fallback. | No |
| `novaic-agent-runtime/task_queue/handlers/runtime_handlers.py` | 2 | `optional` | Documentation-only optional fields | Hit is in payload docstring for `initial_context` and `user_message`; both are current request-shape comments, not live fallback branches. | No |
| `novaic-agent-runtime/task_queue/handlers/session_handlers.py` | 7 | `remaining_stack` | Live expected session finalize validation | `session.ended` validates `remaining_stack` presence/type before calling the session coordinator. This is the explicit-finalize boundary the architecture wants. | No |
| `novaic-agent-runtime/task_queue/handlers/subagent_handlers.py` | 1 | `optional` | Documentation-only optional field | Hit is a docstring for `result`; subagent completion currently sends substance through IM and lifecycle result may be absent. | No |
| `novaic-agent-runtime/task_queue/retry_policy.py` | 1 | `optional` | Documentation-only override | Hit is a docstring for a max-attempts override. Retry policy still has explicit inputs and no hidden fallback branch in this hit. | No |
| `novaic-agent-runtime/task_queue/saga.py` | 5 | `optional` | Risky stale substrate field | `SagaStep.optional` and `add_*_step(optional=...)` exist, but `SagaDefinition.to_dag()` does not propagate `optional` into `DagNode`, and task execution does not consume it for task steps. This is misleading dead semantics rather than a working contract. | Yes |
| `novaic-agent-runtime/task_queue/sagas/wake_finalize.py` | 8 | `remaining_stack`, `optional` | Mixed: live finalize contract plus risky stale optional usage | `remaining_stack` is correct and required. However `WAKE_FINALIZE_SAGA.add_task_step(... optional=True)` relies on the stale optional field above, so it documents behavior that the current DAG worker does not implement. | Yes |
| `novaic-agent-runtime/task_queue/tool_output.py` | 2 | `optional` | Live expected manifest shaping | Local variable `optional` filters artifact metadata fields; this is not queue-session compatibility logic. | No |
| `novaic-agent-runtime/task_queue/utils/cortex_bridge.py` | 4 | `remaining_stack`, `optional` | Live expected bridge contract plus doc comment | `scope_end()` accepts optional bridge parameters but only sends `remaining_stack` when provided by the finalize path; the scanned `task` hit is a docstring for skill_begin. | No |
| `novaic-agent-runtime/task_queue/workers/saga_effects.py` | 2 | `publish` | Live expected effect interpreter boundary | Saga worker interprets a `publish_task` worker effect by calling `TaskQueueClient.publish()`. This is the intended durable task publish boundary. | No |
| `novaic-agent-runtime/task_queue/workers/task_effects.py` | 2 | `publish` | Live expected effect interpreter boundary | Task worker interprets a publish effect through `TaskQueueClient.publish()`. This is the explicit side-effect adapter, not an imperative bypass inside pure decisions. | No |

## Follow-up Candidate

`task_queue/saga.py` and `task_queue/sagas/wake_finalize.py` expose an `optional` step semantic that appears unimplemented in the active DAG execution path. The likely cleanup is to either remove the dead `optional` parameter/field and the `optional=True` call site, or implement optional-step semantics deliberately. Given the current AI-era cleanup direction, deletion is the safer default unless a current test proves the semantic is required.
