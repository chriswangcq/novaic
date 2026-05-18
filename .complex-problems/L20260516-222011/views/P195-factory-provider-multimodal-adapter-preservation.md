# P195: Factory provider multimodal adapter preservation

Status: done
Parent: P190
Root: P000
Source Ticket: T181 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P195
Body: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P195/README.md
Ticket(s): T183

## Problem
Audit LLM Factory/provider adapter code to ensure incoming structured image content is sent to the provider API in the correct schema and is not dropped or textified. Request logs should preserve useful observability without misleadingly showing media as plain text payload.

## Success Criteria
- Map factory/provider adapter code for OpenAI-compatible multimodal messages.
- Prove image content is preserved in the provider request schema.
- Prove raw base64 does not appear inside plain text content.
- Prove request/log detail behavior is accurate enough to debug media calls.
- Add or verify focused adapter/log tests.

## Subproblems
- P196: Factory provider request adapter media preservation
- P197: Factory multimodal log detail serialization

## Results
- R180

## Latest Check
C194

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P195/README.md
- Ticket T183: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P195/tickets/T183.md
- Result R180: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P195/results/R180.md
- Check C194: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P195/checks/C194.md

## Follow-ups
- none
