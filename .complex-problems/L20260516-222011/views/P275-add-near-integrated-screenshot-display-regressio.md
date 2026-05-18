# P275: Add near-integrated screenshot/display regression test

Status: done
Parent: P270
Root: P000
Source Ticket: T268 (split)
Source Check: none
Package: problems/P000/children/P003/children/P132/children/P261/children/P270/children/P275
Body: problems/P000/children/P003/children/P132/children/P261/children/P270/children/P275/README.md
Ticket(s): T269

## Problem
Add the smallest regression that simulates shell screenshot artifact manifest, subsequent display current perception, and later historical display replay.

## Success Criteria
- Test uses explicit fake Cortex bridge responses by tool call and projection.
- Test proves shell manifest stays text-only with artifact display access hint.
- Test proves current display injects provider-native image content.
- Test proves later historical display replay does not inject image content or raw base64.
- Test fails meaningfully if current/historical projection regresses.

## Subproblems
- none

## Results
- R264

## Latest Check
C279

## Bodies
- Problem: problems/P000/children/P003/children/P132/children/P261/children/P270/children/P275/README.md
- Ticket T269: problems/P000/children/P003/children/P132/children/P261/children/P270/children/P275/tickets/T269.md
- Result R264: problems/P000/children/P003/children/P132/children/P261/children/P270/children/P275/results/R264.md
- Check C279: problems/P000/children/P003/children/P132/children/P261/children/P270/children/P275/checks/C279.md

## Follow-ups
- none
