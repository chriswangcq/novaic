# P373: Cortex Archive Diagnostics Persistence

Status: done
Parent: P368
Root: P000
Source Ticket: T359 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P373
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P373/README.md
Ticket(s): T362

## Problem
Cortex archive/context-event records should persist the explicit finalize diagnostics supplied by the runtime boundary, not generic archive reasons or remaining-stack data inferred from current active-stack projection.

## Success Criteria
- Cortex archive code writes explicit `finalize_reason`, `session_generation`, and remaining-stack diagnostics into the appropriate archive/context-event metadata.
- Archive logic does not synthesize finalize generation from active lookup for the finalize diagnostics path.
- Missing or invalid explicit generation cannot produce a finalize-diagnostics archive event.
- Focused Cortex tests prove valid archive metadata and invalid generation rejection.

## Subproblems
- P375: Cortex Archive Diagnostics Persistence Source Map
- P376: Persist Explicit Archive Diagnostics
- P377: Cortex Archive Diagnostics Persistence Verification

## Results
- R358

## Latest Check
C381

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P373/README.md
- Ticket T362: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P373/tickets/T362.md
- Result R358: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P373/results/R358.md
- Check C381: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P373/checks/C381.md

## Follow-ups
- none
