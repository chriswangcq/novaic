# P612: UI Monitor and Log Artifact Display Boundary

Status: done
Parent: P602
Root: P000
Source Ticket: T603 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P602/children/P612
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P602/children/P612/README.md
Ticket(s): T605

## Problem
Audit UI monitor/log display surfaces that could present artifact or tool output data, including Agent Monitor and LLM Factory logs, and prove they are bounded/escaped/display-only rather than raw image-byte UI paths.

## Success Criteria
- Records exact scans for monitor/log artifact, raw JSON, request/response body, image, and base64 rendering paths.
- Cites UI/backend static slices that bound or escape display content.
- Reuses P604 evidence where appropriate but explicitly maps it to this broader UI display problem.
- Creates a follow-up if monitor/log UI surfaces render raw unredacted image bytes in normal display paths.

## Subproblems
- none

## Results
- R598

## Latest Check
C639

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P602/children/P612/README.md
- Ticket T605: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P602/children/P612/tickets/T605.md
- Result R598: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P602/children/P612/results/R598.md
- Check C639: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P602/children/P612/checks/C639.md

## Follow-ups
- none
