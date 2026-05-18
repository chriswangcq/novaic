# P168: ReactThink llm.call payload builder map

Status: done
Parent: P161
Root: P000
Source Ticket: T153 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P168
Body: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P168/README.md
Ticket(s): T154

## Problem
`react_think` is responsible for moving the prepared Cortex snapshot into the `llm.call` task payload. The field copy contract must be explicit so final LLM calls do not accidentally use stale local context fields.

## Success Criteria
- `novaic-agent-runtime/task_queue/contracts/react_think.py` is mapped for `build_llm_call_payload`.
- The fields copied from `prepare_context_result` into the LLM call payload are listed with line pointers.
- Existing or added tests prove `messages` and `tools` are copied from the prepare result, not from saga-local continuity fields.
- Any ambiguous local fallback in this builder is fixed or split.

## Subproblems
- none

## Results
- R149

## Latest Check
C163

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P168/README.md
- Ticket T154: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P168/tickets/T154.md
- Result R149: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P168/results/R149.md
- Check C163: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P168/checks/C163.md

## Follow-ups
- none
