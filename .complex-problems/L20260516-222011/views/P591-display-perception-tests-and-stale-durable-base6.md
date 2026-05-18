# P591: Display perception tests and stale durable-base64 cleanup

Status: done
Parent: P586
Root: P000
Source Ticket: T576 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P591
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P591/README.md
Ticket(s): T581

## Problem
Tests currently encode the old durable-base64 contract. After runtime/Cortex/resolver changes, tests must prove the new contract and remove stale assertions or helper code that implies display bytes belong in durable Cortex payloads.

## Success Criteria
- Unit tests prove runtime durable display payload contains BlobRef references and no base64 `data`.
- Cortex projection tests prove BlobRef image references survive `display_perception` and remain text-only in history.
- Runtime expansion tests prove current display refs become provider image input and historical refs do not.
- Targeted searches show no active test or code path expects `durable_payload.llm_content._mcp_content[].data` for display.
- Focused test commands pass.

## Subproblems
- none

## Results
- R574

## Latest Check
C611

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P591/README.md
- Ticket T581: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P591/tickets/T581.md
- Result R574: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P591/results/R574.md
- Check C611: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P591/checks/C611.md

## Follow-ups
- none
