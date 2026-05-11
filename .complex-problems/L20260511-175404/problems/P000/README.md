# Live HD screenshot wake stalls after tool completion

## Problem

Production Agent UI shows the latest user message “再试一下” delivered, and the monitor popup shows the agent reached “尝试 HD 截图 完成”, but the conversation appears stuck without a final user-visible answer. This should not be treated as a deploy availability issue because `./deploy status` reports all backend services and workers healthy. We need determine the concrete state-machine/log/queue cause and fix it if code/config is responsible.

## Success Criteria

- Identify the exact production wake/session/saga/task state corresponding to the stuck UI.
- Determine whether the stall is in Runtime control flow, Queue/Saga state, Cortex tool result persistence, shell/device capability behavior, or frontend projection.
- Provide evidence from logs or durable state, not guesses.
- If a code/config bug is found, implement and test the fix.
- If no code change is needed, explain the operational cause and recovery action.
