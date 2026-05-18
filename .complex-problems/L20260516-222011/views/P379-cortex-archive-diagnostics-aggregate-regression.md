# P379: Cortex archive diagnostics aggregate regression

Status: done
Parent: P339
Root: P000
Source Ticket: T368 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P379
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P379/README.md
Ticket(s): T372

## Problem
Cortex scope-end and context-event lifecycle behavior needs a focused regression pass to prove archive diagnostics use explicit request payloads rather than implicit active state, preserve context projection semantics, and reject unsafe generation coercion.

## Success Criteria
- Focused Cortex lifecycle, scope archive, projection, model, and write-authority tests pass.
- Source guards prove archive diagnostics do not look up current active generation or synthesize remaining stack from hidden state.
- Bool or missing `session_generation` diagnostics behavior is verified as fail-closed where diagnostics are present.
- Any unsafe Cortex hit is fixed or converted into a follow-up problem.

## Subproblems
- P383: Cortex archive diagnostics focused tests
- P384: Cortex archive diagnostics source guard classification

## Results
- R368

## Latest Check
C391

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P379/README.md
- Ticket T372: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P379/tickets/T372.md
- Result R368: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P379/results/R368.md
- Check C391: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P379/checks/C391.md

## Follow-ups
- none
