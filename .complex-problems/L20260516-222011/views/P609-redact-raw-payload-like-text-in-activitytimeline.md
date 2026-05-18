# P609: Redact raw payload-like text in ActivityTimeline details

Status: done
Parent: P606
Root: P000
Source Ticket: none (none)
Source Check: C629
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P606/children/P609
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P606/children/P609/README.md
Ticket(s): T599

## Problem
Add a frontend safety boundary so ActivityTimeline does not render raw base64-like or data-url-like image payload text in either collapsed preview or expanded inline details, even if an upstream monitor record accidentally contains such text.

## Success Criteria
- `ActivityTimeline.tsx` detects obvious raw payload-like strings such as `data:image/*;base64,` and long base64/JPEG-prefix text.
- Such payload-like text is replaced with a short safe message, preferably pointing to saved payload/artifact availability when `has_payload` is true.
- Focused tests prove collapsed and expanded ActivityTimeline views do not expose raw base64-like payload text.
- Existing ActivityTimeline tests still pass.

## Subproblems
- none

## Results
- R591

## Latest Check
C630

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P606/children/P609/README.md
- Ticket T599: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P606/children/P609/tickets/T599.md
- Result R591: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P606/children/P609/results/R591.md
- Check C630: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P606/children/P609/checks/C630.md

## Follow-ups
- none
