# P126: Context assembly source map and event boundary

Status: done
Parent: P003
Root: P000
Source Ticket: T121 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126
Body: problems/P000/children/P003/children/P126/README.md
Ticket(s): T122

## Problem
The Cortex context assembly path spans event store, workspace projections, step references, payload references, and active stack injection. Before changing behavior, the active path must be mapped with concrete file/function pointers so optimization work does not patch the wrong layer or leave an old branch active.

## Success Criteria
- The active context assembly/write/read path is mapped from incoming step/result writes to LLM context preparation.
- Each mapped file/function is classified as active, test-only, compatibility-only, or dead/stale.
- The role of context event stream, workspace projections, `step_ref`, `payload_ref`, and active skill stack injection is documented.
- Any discovered duplicate or stale assembly path is turned into a follow-up child problem or removed if obviously dead and safe.
- Focused tests or static checks cover any mapping assumption that affects runtime behavior.

## Subproblems
- P133: ContextEvent stream and read model map
- P134: Workspace materialized projections and payload reference map
- P135: Runtime prepare-context handler map
- P136: Tool result step_ref and payload_ref map
- P137: Active skill stack injection map

## Results
- R171

## Latest Check
C185

## Bodies
- Problem: problems/P000/children/P003/children/P126/README.md
- Ticket T122: problems/P000/children/P003/children/P126/tickets/T122.md
- Result R171: problems/P000/children/P003/children/P126/results/R171.md
- Check C185: problems/P000/children/P003/children/P126/checks/C185.md

## Follow-ups
- none
