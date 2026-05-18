# P814: Child Problem: AssistantMessage legacy events rendering cleanup

Status: done
Parent: P786
Root: P000
Source Ticket: T804 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P814
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P814/README.md
Ticket(s): T811

## Problem
`novaic-app/src/components/Chat/AssistantMessage.tsx` contains legacy event rendering paths that may stringify non-string event content or render broad event payloads. Inactive legacy paths should not be able to display raw JSON/base64/payload-like content.

## Success Criteria
- Legacy `events` rendering is removed if no longer live.
- If a narrow event path is still required, it only renders safe, bounded text projections.
- `JSON.stringify` fallback rendering is removed or guarded for this chat surface.
- Focused chat/component tests pass for touched behavior.

## Subproblems
- none

## Results
- R802

## Latest Check
C851

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P814/README.md
- Ticket T811: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P814/tickets/T811.md
- Result R802: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P814/results/R802.md
- Check C851: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P814/checks/C851.md

## Follow-ups
- none
