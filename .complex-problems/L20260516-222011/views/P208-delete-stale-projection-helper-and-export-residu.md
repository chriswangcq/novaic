# P208: Delete stale projection helper and export residue

Status: done
Parent: P199
Root: P000
Source Ticket: T195 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P208
Body: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P208/README.md
Ticket(s): T197

## Problem
The stale `resolve_for_llm` helper can inline image/base64 payloads into text-oriented LLM context. Once caller verification proves it is dead in production, remove the helper, any now-unused imports, and any package exports that point to it.

## Success Criteria
- Stale helper code is physically removed from production files.
- Unused imports/exports left by the deletion are removed.
- Remaining production projection APIs still import cleanly.
- Focused Cortex projection tests pass after deletion.

## Subproblems
- none

## Results
- R192

## Latest Check
C206

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P208/README.md
- Ticket T197: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P208/tickets/T197.md
- Result R192: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P208/results/R192.md
- Check C206: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P208/checks/C206.md

## Follow-ups
- none
