# P087: App device WebRTC and UI media residue classification

Status: done
Parent: P085
Root: P000
Source Ticket: T077 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P085/children/P087
Body: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P085/children/P087/README.md
Ticket(s): T079

## Problem
`novaic-app/src` contains device polling fallback logic, software cursor fallback wording, WebRTC RGBA base64 handling, and other browser/device media mechanics. These may be necessary UI mechanics rather than stale compatibility paths, but they need explicit classification.

## Success Criteria
- Inspect device polling, software cursor, WebRTC, and image/media utility hits for fallback/base64/data URL wording.
- Classify each as current browser/device behavior, guard/test fixture, stale residue, or active risk.
- Apply safe comment/name cleanup where wording incorrectly suggests old compatibility behavior.
- Run focused tests or explicit no-code-change verification for touched device/media code.

## Subproblems
- none

## Results
- R074

## Latest Check
C087

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P085/children/P087/README.md
- Ticket T079: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P085/children/P087/tickets/T079.md
- Result R074: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P085/children/P087/results/R074.md
- Check C087: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P085/children/P087/checks/C087.md

## Follow-ups
- none
