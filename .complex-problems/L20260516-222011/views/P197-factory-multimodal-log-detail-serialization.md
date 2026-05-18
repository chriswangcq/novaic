# P197: Factory multimodal log detail serialization

Status: done
Parent: P195
Root: P000
Source Ticket: T183 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P195/children/P197
Body: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P195/children/P197/README.md
Ticket(s): T185

## Problem
Audit Factory log/detail serialization for multimodal calls. The log UI/API should show useful request/response structure without collapsing calls to `{}` or presenting media as misleading plain text.

## Success Criteria
- Locate Factory logging/detail API and persistence schema for request/response bodies.
- Prove multimodal request details retain enough structured information to debug calls.
- Prove large/base64 media is redacted or represented safely, not rendered as a giant text blob.
- Add or verify focused log/detail tests.

## Subproblems
- none

## Results
- R179

## Latest Check
C193

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P195/children/P197/README.md
- Ticket T185: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P195/children/P197/tickets/T185.md
- Result R179: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P195/children/P197/results/R179.md
- Check C193: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P195/children/P197/checks/C193.md

## Follow-ups
- none
