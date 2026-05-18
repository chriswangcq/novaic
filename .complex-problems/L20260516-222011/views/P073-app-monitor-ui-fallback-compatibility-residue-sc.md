# P073: App monitor UI fallback compatibility residue scan

Status: done
Parent: P071
Root: P000
Source Ticket: T064 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P073
Body: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P073/README.md
Ticket(s): T065

## Problem
App monitor/UI code and tests may still normalize old direct tool names or contain legacy/fallback wording that is no longer part of the final shell-first architecture.

## Success Criteria
- Focused scans cover `novaic-app/src` for legacy, fallback, compat, TODO/FIXME, direct tool names, and shell/display wording.
- Hits are classified as active UI behavior, test fixture, localization/product text, or stale residue.
- Safe tiny cleanup is applied directly if found.
- Focused frontend tests/lint pass for touched files.

## Subproblems
- none

## Results
- R059

## Latest Check
C071

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P073/README.md
- Ticket T065: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P073/tickets/T065.md
- Result R059: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P073/results/R059.md
- Check C071: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P073/checks/C071.md

## Follow-ups
- none
