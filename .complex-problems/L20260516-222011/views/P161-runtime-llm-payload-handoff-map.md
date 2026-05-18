# P161: Runtime LLM payload handoff map

Status: done
Parent: P135
Root: P000
Source Ticket: T146 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P135/children/P161
Body: problems/P000/children/P003/children/P126/children/P135/children/P161/README.md
Ticket(s): T153

## Problem
The final LLM request should be assembled from the prepared Cortex snapshot, not from stale context projections or ad hoc local fields. The exact handoff through `react_think` contracts and LLM handlers must be mapped and guarded.

## Success Criteria
- `novaic-agent-runtime/task_queue/contracts/react_think.py` and `novaic-agent-runtime/task_queue/handlers/llm_handlers.py` are mapped for `build_llm_call_payload` and final provider-message assembly.
- The fields copied from prepare-context result into `llm.call` input are documented.
- Tests or static guards prove final provider messages/tools come from the prepared snapshot.
- Any legacy local context input that still reaches provider messages is fixed or split.

## Subproblems
- P168: ReactThink llm.call payload builder map
- P169: LLM handler provider request assembly map
- P170: LLM payload handoff regression coverage audit

## Results
- R154

## Latest Check
C168

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P135/children/P161/README.md
- Ticket T153: problems/P000/children/P003/children/P126/children/P135/children/P161/tickets/T153.md
- Result R154: problems/P000/children/P003/children/P126/children/P135/children/P161/results/R154.md
- Check C168: problems/P000/children/P003/children/P126/children/P135/children/P161/checks/C168.md

## Follow-ups
- none
