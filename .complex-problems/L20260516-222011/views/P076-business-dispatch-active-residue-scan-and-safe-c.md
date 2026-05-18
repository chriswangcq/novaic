# P076: Business dispatch active residue scan and safe cleanup

Status: done
Parent: P074
Root: P000
Source Ticket: T066 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/children/P076
Body: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/children/P076/README.md
Ticket(s): T067

## Problem
The business dispatch adapter code needs a focused active-path scan for fallback/compatibility/migration/TODO/direct-tool residue. The scan must classify every hit and only apply safe cleanup that does not change queue/FSM dispatch behavior.

## Success Criteria
- Scan `novaic-business` active implementation and relevant focused tests for `legacy`, `fallback`, `compat`, `migration`, `TODO`, `FIXME`, and direct tool terms such as `im_read`, `im_reply`, `payload_read`, `audio_qa`, and `subagent_spawn`.
- Inspect each non-obvious hit and classify it as active-risk, safe cleanup, guard/test-only, or unrelated domain terminology.
- Apply safe comment/dead-code cleanup directly where it removes misleading residue without behavior changes.
- Run focused business tests for touched files, or explicitly record any unavailable test path.
- Produce a result that maps changes and classifications back to this checklist.

## Subproblems
- P077: Finish Business residue classification, cleanup, and tests

## Results
- R060

## Latest Check
C078

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/children/P076/README.md
- Ticket T067: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/children/P076/tickets/T067.md
- Result R060: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/children/P076/results/R060.md
- Check C072: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/children/P076/checks/C072.md
- Check C078: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/children/P076/checks/C078.md

## Follow-ups
- P077: Finish Business residue classification, cleanup, and tests
