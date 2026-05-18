# P066: Active code fallback and compatibility residue scan

Status: done
Parent: P017
Root: P000
Source Ticket: T059 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P017/children/P066
Body: problems/P000/children/P001/children/P009/children/P017/children/P066/README.md
Ticket(s): T060

## Problem
Active implementation code may still contain stale fallback, compatibility, legacy, or migration branches that preserve old behavior after the newer queue/FSM/shell/display/blob contracts were introduced.

## Success Criteria
- Focused scans cover active implementation directories while excluding ledger/build/cache noise.
- Hits are classified as active risk, intentional guard, benign adapter, or historical residue.
- Tiny high-confidence cleanup is applied directly if safe.
- Larger active-risk branches are routed to follow-up or spawned child problems instead of being summarized away.

## Subproblems
- P069: Runtime queue fallback compatibility residue scan
- P070: Cortex common fallback compatibility residue scan
- P071: App business MCP adapter fallback compatibility residue scan
- P085: Classify and clean non-monitor App active residue

## Results
- R072

## Latest Check
C091

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P017/children/P066/README.md
- Ticket T060: problems/P000/children/P001/children/P009/children/P017/children/P066/tickets/T060.md
- Result R072: problems/P000/children/P001/children/P009/children/P017/children/P066/results/R072.md
- Check C085: problems/P000/children/P001/children/P009/children/P017/children/P066/checks/C085.md
- Check C091: problems/P000/children/P001/children/P009/children/P017/children/P066/checks/C091.md

## Follow-ups
- P085: Classify and clean non-monitor App active residue
