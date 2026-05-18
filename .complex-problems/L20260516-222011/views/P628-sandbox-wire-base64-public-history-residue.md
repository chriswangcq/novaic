# P628: Sandbox Wire Base64 Public-History Residue

Status: done
Parent: P622
Root: P000
Source Ticket: T623 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P565/children/P622/children/P628
Body: problems/P000/children/P005/children/P553/children/P565/children/P622/children/P628/README.md
Ticket(s): T624

## Problem
Classify base64/stdout_b64/stderr_b64 handling across SDK/service/Cortex/shell projection to confirm bytes stay in private wire or durable payloads and do not leak into LLM history/tool text.

## Success Criteria
- Records exact scans for base64/stdout_b64/stderr_b64/data URL/image payload terms.
- Cites SDK/service/Cortex/runtime projection slices.
- Classifies private wire encoding vs public history leakage.
- Runs focused shell/artifact projection tests.
- Creates follow-up if public LLM history can receive raw base64 bytes.

## Subproblems
- none

## Results
- R619

## Latest Check
C660

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P565/children/P622/children/P628/README.md
- Ticket T624: problems/P000/children/P005/children/P553/children/P565/children/P622/children/P628/tickets/T624.md
- Result R619: problems/P000/children/P005/children/P553/children/P565/children/P622/children/P628/results/R619.md
- Check C660: problems/P000/children/P005/children/P553/children/P565/children/P622/children/P628/checks/C660.md

## Follow-ups
- none
