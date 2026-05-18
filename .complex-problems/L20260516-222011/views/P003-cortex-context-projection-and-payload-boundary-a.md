# P003: Cortex context projection and payload boundary audit

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T121

## Problem
Audit and optimize Cortex context assembly, event-source projection, display/image projection, durable payload references, active skill stack injection, and large-output boundaries so LLM context remains pointer-oriented and media-aware.

## Success Criteria
- Current context assembly code paths are mapped.
- Display/image projection and historical tool-output behavior are verified.
- Large payload/base64/text leakage paths are searched and fixed if active.
- Targeted tests verify current-round image projection and historical manifest-only behavior.

## Subproblems
- P126: Context assembly source map and event boundary
- P127: Step result projection contract audit
- P128: Agent runtime context client and history expansion audit
- P129: Payload API and pointer retrieval boundary audit
- P130: Provider-native media adapter boundary audit
- P131: Large-output and base64 leakage sweep
- P132: Cross-layer context projection regression suite

## Results
- R271

## Latest Check
C286

## Bodies
- Problem: problems/P000/children/P003/README.md
- Ticket T121: problems/P000/children/P003/tickets/T121.md
- Result R271: problems/P000/children/P003/results/R271.md
- Check C286: problems/P000/children/P003/checks/C286.md

## Follow-ups
- none
