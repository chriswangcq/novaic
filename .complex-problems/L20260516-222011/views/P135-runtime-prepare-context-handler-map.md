# P135: Runtime prepare-context handler map

Status: done
Parent: P126
Root: P000
Source Ticket: T122 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P135
Body: problems/P000/children/P003/children/P126/children/P135/README.md
Ticket(s): T146

## Problem
Agent runtime decides when Cortex context is prepared and passed to the LLM. This handler chain must be mapped to ensure the live LLM request uses the intended ContextEvent-backed snapshot and not stale local continuity.

## Success Criteria
- `cortex_handlers.py`, `runtime_handlers.py`, `context_handlers.py`, `react_think.py`, and `react_think` contracts are mapped around prepare-context.
- The exact handoff between queue saga steps, Cortex prepare response, and LLM handler input is documented.
- Any remaining local cross-wake continuity path is classified as active-safe, dead, or stale.
- Relevant runtime tests or static checks are run for prepare-context assumptions.

## Subproblems
- P159: Runtime saga prepare-context ordering map
- P160: Runtime Cortex prepare handler contract map
- P161: Runtime LLM payload handoff map
- P162: Runtime continuity and context.read residue classification
- P163: Runtime prepare-context regression coverage audit

## Results
- R160

## Latest Check
C174

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P135/README.md
- Ticket T146: problems/P000/children/P003/children/P126/children/P135/tickets/T146.md
- Result R160: problems/P000/children/P003/children/P126/children/P135/results/R160.md
- Check C174: problems/P000/children/P003/children/P126/children/P135/checks/C174.md

## Follow-ups
- none
