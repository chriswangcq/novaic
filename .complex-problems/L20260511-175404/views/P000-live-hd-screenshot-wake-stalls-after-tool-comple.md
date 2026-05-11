# P000: Live HD screenshot wake stalls after tool completion

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Production Agent UI shows the latest user message “再试一下” delivered, and the monitor popup shows the agent reached “尝试 HD 截图 完成”, but the conversation appears stuck without a final user-visible answer. This should not be treated as a deploy availability issue because `./deploy status` reports all backend services and workers healthy. We need determine the concrete state-machine/log/queue cause and fix it if code/config is responsible.

## Success Criteria
- Identify the exact production wake/session/saga/task state corresponding to the stuck UI.
- Determine whether the stall is in Runtime control flow, Queue/Saga state, Cortex tool result persistence, shell/device capability behavior, or frontend projection.
- Provide evidence from logs or durable state, not guesses.
- If a code/config bug is found, implement and test the fix.
- If no code change is needed, explain the operational cause and recovery action.

## Subproblems
- P001: Identify exact stuck production state
- P002: Determine root cause and required fix
- P003: Verify HD screenshot wake recovery

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R003: problems/P000/results/R003.md
- Check C003: problems/P000/checks/C003.md

## Follow-ups
- none
