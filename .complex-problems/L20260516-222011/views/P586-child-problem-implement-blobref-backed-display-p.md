# P586: Child Problem: Implement BlobRef-backed display perception

Status: done
Parent: P584
Root: P000
Source Ticket: T574 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/README.md
Ticket(s): T576

## Problem
Change display durable payload and projection code so durable display payloads keep BlobRef metadata instead of inline image bytes, while current display perception still emits provider image content.

## Success Criteria
- Runtime display durable payload has no image `data` base64.
- Perception projection resolves BlobRef on demand or uses an explicit media resolver to produce image MCP content for current display perception.
- Public/history projections remain text-only.
- Obsolete tests expecting durable base64 are rewritten or deleted.

## Subproblems
- P588: Runtime display durable payload is BlobRef-only
- P589: Cortex display projection preserves media references
- P590: Runtime resolves current display image refs for LLM calls
- P591: Display perception tests and stale durable-base64 cleanup

## Results
- R575

## Latest Check
C612

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/README.md
- Ticket T576: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/tickets/T576.md
- Result R575: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/results/R575.md
- Check C612: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/checks/C612.md

## Follow-ups
- none
