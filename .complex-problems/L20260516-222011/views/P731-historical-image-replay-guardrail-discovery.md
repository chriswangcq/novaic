# P731: Historical image replay guardrail discovery

Status: done
Parent: P726
Root: P000
Source Ticket: T717 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P726/children/P731
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P726/children/P731/README.md
Ticket(s): T720

## Problem
Discover whether prior display/image tool outputs are replayed into later LLM requests as text-only manifest/history content rather than provider image content or raw base64, except when current-round display projection explicitly loads an image.

## Success Criteria
- History replay guardrail tests are identified with file pointers.
- Current-round display projection is distinguished from historical replay behavior.
- Any missing test or active replay violation is listed as a remediation candidate.

## Subproblems
- none

## Results
- R711

## Latest Check
C755

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P726/children/P731/README.md
- Ticket T720: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P726/children/P731/tickets/T720.md
- Result R711: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P726/children/P731/results/R711.md
- Check C755: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P726/children/P731/checks/C755.md

## Follow-ups
- none
