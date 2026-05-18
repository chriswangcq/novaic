# P587: Child Problem: Verify display durable no-base64 and image delivery

Status: done
Parent: P584
Root: P000
Source Ticket: T574 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P587
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P587/README.md
Ticket(s): T582

## Problem
Run focused tests and static scans proving display durable payloads no longer store inline image bytes, while provider requests still receive current display images and history replay stays text-only.

## Success Criteria
- Focused runtime and Cortex display projection tests pass.
- Static scans do not find tests or code requiring `durable_payload.llm_content._mcp_content[].data`.
- Evidence artifacts record commands and outputs.

## Subproblems
- none

## Results
- R576

## Latest Check
C613

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P587/README.md
- Ticket T582: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P587/tickets/T582.md
- Result R576: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P587/results/R576.md
- Check C613: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P587/checks/C613.md

## Follow-ups
- none
