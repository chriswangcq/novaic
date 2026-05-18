# P194: Runtime-to-factory multimodal request preservation

Status: done
Parent: P190
Root: P000
Source Ticket: T181 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P194
Body: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P194/README.md
Ticket(s): T182

## Problem
Audit the runtime LLM transport boundary to ensure prepared messages containing provider-shaped image content are sent to LLM Factory without being stringified, flattened, or converted to plain text.

## Success Criteria
- Map runtime LLM transport/client request builder.
- Prove prepared OpenAI image content reaches the factory request body as structured content.
- Prove raw base64 is not moved into a plain text field by runtime serialization.
- Add or verify focused tests for runtime-to-factory multimodal request payloads.

## Subproblems
- none

## Results
- R177

## Latest Check
C191

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P194/README.md
- Ticket T182: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P194/tickets/T182.md
- Result R177: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P194/results/R177.md
- Check C191: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P194/checks/C191.md

## Follow-ups
- none
