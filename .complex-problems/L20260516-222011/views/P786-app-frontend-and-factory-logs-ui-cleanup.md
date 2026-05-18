# P786: App Frontend And Factory Logs UI Cleanup

Status: done
Parent: P750
Root: P000
Source Ticket: T774 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/README.md
Ticket(s): T804

## Problem
Remove or narrow frontend/log UI residue that can expose raw payloads or mislead future agent work despite active chat/monitor paths being mostly clean.

## Success Criteria
- `novaic-llm-factory/static/factory-logs.html` applies safe client-side scrub/projection for raw request/response/message/tool detail rendering.
- Unused `novaic-app/src/components/Visual/SmartValue.tsx` is deleted if still unused.
- Legacy `events` rendering in `novaic-app/src/components/Chat/AssistantMessage.tsx` is removed or narrowed so inactive paths cannot render raw JSON/base64/payload-like content.
- Focused frontend tests/lints pass for touched app surfaces.

## Subproblems
- P812: Child Problem: Factory logs safe payload projection
- P813: Child Problem: SmartValue unused raw renderer cleanup
- P814: Child Problem: AssistantMessage legacy events rendering cleanup
- P815: Child Problem: Frontend payload residue aggregate verification

## Results
- R804

## Latest Check
C853

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/README.md
- Ticket T804: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/tickets/T804.md
- Result R804: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/results/R804.md
- Check C853: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/checks/C853.md

## Follow-ups
- none
