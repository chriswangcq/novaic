# Task contracts and handler residue cleanup

## Problem

Task/saga contracts and handlers (`react_think`, `react_actions`, `wake_finalize`, `subagent_wake`, `session_handlers`, `cortex_handlers`, `cortex_bridge`) contain round, stack-depth, session-generation, and archive/finalize hits. They must be classified or patched so task-level defaults cannot weaken live session generation boundaries.

## Success Criteria

- Inspect all task contract, saga, handler, and Cortex bridge hits from P402.
- Patch dangerous session-generation defaults or stale archive/finalize behavior.
- Classify round/stack-depth/tool-retry counters as safe only with file evidence.
- Add focused tests for any patched task contract or handler boundary.
- Rerun task/handler guard searches and focused tests.
