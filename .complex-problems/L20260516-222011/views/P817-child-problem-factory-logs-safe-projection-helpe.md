# P817: Child Problem: Factory logs safe projection helper

Status: done
Parent: P812
Root: P000
Source Ticket: T805 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/children/P817
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/children/P817/README.md
Ticket(s): T807

## Problem
`factory-logs.html` needs a reusable client-side helper that summarizes unsafe values consistently instead of each renderer inventing its own truncation behavior.

## Success Criteria
- A local helper detects and summarizes long strings, base64-like strings, large arrays, large objects, and known payload-ish keys.
- The helper keeps compact values and BlobRefs readable.
- The helper output is deterministic and simple enough to test without a frontend build.

## Subproblems
- none

## Results
- R797

## Latest Check
C846

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/children/P817/README.md
- Ticket T807: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/children/P817/tickets/T807.md
- Result R797: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/children/P817/results/R797.md
- Check C846: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/children/P817/checks/C846.md

## Follow-ups
- none
