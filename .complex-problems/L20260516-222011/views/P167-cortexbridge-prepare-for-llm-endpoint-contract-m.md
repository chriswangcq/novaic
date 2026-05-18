# P167: CortexBridge prepare_for_llm endpoint contract map

Status: done
Parent: P160
Root: P000
Source Ticket: T150 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P135/children/P160/children/P167
Body: problems/P000/children/P003/children/P126/children/P135/children/P160/children/P167/README.md
Ticket(s): T152

## Problem
`CortexBridge.prepare_for_llm` is the runtime client boundary for the ContextEvent-backed prepare endpoint. It must call the correct Cortex API with explicit tenant fields and not silently fall back to materialized context reads.

## Success Criteria
- `cortex_bridge.py` `prepare_for_llm` is mapped with line pointers for endpoint path and payload fields.
- The return/passthrough shape is documented.
- Any bridge fallback to `read_context` for prepare is classified and fixed or split if active.
- Focused bridge/handler tests are identified and run.

## Subproblems
- none

## Results
- R147

## Latest Check
C161

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P135/children/P160/children/P167/README.md
- Ticket T152: problems/P000/children/P003/children/P126/children/P135/children/P160/children/P167/tickets/T152.md
- Result R147: problems/P000/children/P003/children/P126/children/P135/children/P160/children/P167/results/R147.md
- Check C161: problems/P000/children/P003/children/P126/children/P135/children/P160/children/P167/checks/C161.md

## Follow-ups
- none
