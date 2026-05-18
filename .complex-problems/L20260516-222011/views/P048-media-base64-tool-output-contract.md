# P048: Media/base64 tool output contract

Status: done
Parent: P016
Root: P000
Source Ticket: T039 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P016/children/P048
Body: problems/P000/children/P001/children/P009/children/P016/children/P048/README.md
Ticket(s): T041

## Problem
Device/display/media tool output must not leak large base64 payloads into shell text or LLM context. It should use concise terminal text plus blob/artifact manifests.

## Success Criteria
- Device screenshot/media CLI returns blob/artifact manifest rather than raw base64 text.
- Display/image projection does not serialize base64 as text in LLM messages.
- Focused tests or scans prove the contract.

## Subproblems
- P050: Child Problem: media CLI emits manifests, not bytes
- P051: Child Problem: display and LLM image projection avoids text base64
- P052: Child Problem: shell observations stay terminal-shaped
- P053: Child Problem: base64 leakage regression guards

## Results
- R051

## Latest Check
C063

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P016/children/P048/README.md
- Ticket T041: problems/P000/children/P001/children/P009/children/P016/children/P048/tickets/T041.md
- Result R051: problems/P000/children/P001/children/P009/children/P016/children/P048/results/R051.md
- Check C063: problems/P000/children/P001/children/P009/children/P016/children/P048/checks/C063.md

## Follow-ups
- none
