# P033: Follow-up: classify and isolate remaining direct-tool vocabulary

Status: done
Parent: P015
Root: P000
Source Ticket: none (none)
Source Check: C030
Package: problems/P000/children/P001/children/P009/children/P015/children/P033
Body: problems/P000/children/P001/children/P009/children/P015/children/P033/README.md
Ticket(s): T025

## Problem
The direct-tool cleanup is not fully closed. A fresh scan still finds `im_read`, `im_reply`, payload direct tools, `audio_qa`, and `subagent_spawn` in current code/tests. Some references are legitimate policy/legacy fixtures, but they are not yet isolated enough to prove that the active shell-first contract is clean.

## Success Criteria
- Current-contract tests use `shell`, `display`, `skill_begin`, `skill_end`, or `sleep` examples unless they are explicitly testing legacy/migration behavior.
- Historical direct-tool fixtures are named as legacy/historical fixtures, not generic active-path examples.
- Runtime activity projection keeps historical readability without presenting legacy direct tools as active executor vocabulary.
- A focused scan report classifies all remaining direct-tool names into one of:
- migration policy allowlist,
- legacy historical fixture,
- internal API endpoint/function,
- removed.
- Focused unit tests for the touched modules pass.

## Subproblems
- P034: Policy and API vocabulary classification
- P035: Test fixture vocabulary cleanup
- P036: Monitor activity projection legacy boundary
- P037: Final direct-tool residue scan and exception ledger

## Results
- R035

## Latest Check
C044

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P015/children/P033/README.md
- Ticket T025: problems/P000/children/P001/children/P009/children/P015/children/P033/tickets/T025.md
- Result R035: problems/P000/children/P001/children/P009/children/P015/children/P033/results/R035.md
- Check C044: problems/P000/children/P001/children/P009/children/P015/children/P033/checks/C044.md

## Follow-ups
- none
