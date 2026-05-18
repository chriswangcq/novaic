# P190: Provider media adapter conversion

Status: done
Parent: P185
Root: P000
Source Ticket: T176 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P185/children/P190
Body: problems/P000/children/P003/children/P127/children/P185/children/P190/README.md
Ticket(s): T181

## Problem
Audit the final provider request conversion for current display media. Internal display/media content must become provider-consumable image input according to the target LLM API schema, not a text string containing blob refs or base64.

## Success Criteria
- Map provider adapter code that converts internal multimodal content to final API request messages.
- Prove current display blob input becomes provider image/media content in the request body.
- Prove no raw base64 text is present in provider text fields.
- Fix or create follow-up work for any provider adapter that drops or textifies current display media.

## Subproblems
- P194: Runtime-to-factory multimodal request preservation
- P195: Factory provider multimodal adapter preservation

## Results
- R181

## Latest Check
C195

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P185/children/P190/README.md
- Ticket T181: problems/P000/children/P003/children/P127/children/P185/children/P190/tickets/T181.md
- Result R181: problems/P000/children/P003/children/P127/children/P185/children/P190/results/R181.md
- Check C195: problems/P000/children/P003/children/P127/children/P185/children/P190/checks/C195.md

## Follow-ups
- none
