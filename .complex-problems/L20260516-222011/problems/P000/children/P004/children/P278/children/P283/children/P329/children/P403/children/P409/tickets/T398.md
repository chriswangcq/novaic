# Task contracts and handler cleanup ticket

## Problem Definition

Task contracts, sagas, handlers, and Cortex bridge code contain generation-like, round, stack-depth, retry, archive, and finalize hits. These need classification and cleanup so task-level defaults cannot weaken live session-generation boundaries.

## Proposed Solution

Inspect the P402 hits in:

- `novaic-agent-runtime/task_queue/contracts/react_think.py`
- `novaic-agent-runtime/task_queue/contracts/react_actions.py`
- `novaic-agent-runtime/task_queue/sagas/wake_finalize.py`
- `novaic-agent-runtime/task_queue/sagas/subagent_wake.py`
- `novaic-agent-runtime/task_queue/handlers/session_handlers.py`
- `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py`
- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`
- related React saga files if they appear in guards

Patch dangerous session-generation defaults, classify round/stack/retry counters, and verify handler contracts still fail closed for malformed session identity.

## Acceptance Criteria

- Every task contract, saga, handler, and bridge hit from P402 is classified.
- Live session generation is never defaulted or inferred in task/handler code.
- Round, stack-depth, tool-retry, and Cortex counter values are classified as non-session authority or patched if they affect session mutation.
- Focused task/handler/contract tests pass.

## Verification Plan

- Run targeted guards over the task contract/handler file set.
- Inspect source around every hit cluster.
- Run tests for runtime explicit contracts, finalize ownership/session handlers, subagent/wake finalize contracts, Cortex bridge/handler behavior, and shell/tool contract tests if relevant.

## Risks

- `round_num`, `stack_depth`, and retry counters are legitimate agent loop control state; deleting them because they look like generation defaults would be harmful.
- `session_generation` in task context must remain strict; any fallback to zero/one should be treated as dangerous unless proven unreachable and guarded.

## Assumptions

- Session identity values should be explicit and validated at task/handler boundaries.
- Non-session counters may remain if clearly classified.
