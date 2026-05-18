# P020: Subagent and audio direct tool residue scan

Status: done
Parent: P015
Root: P000
Source Ticket: T009 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P015/children/P020
Body: problems/P000/children/P001/children/P009/children/P015/children/P020/README.md
Ticket(s): T014

## Problem
Search for active direct LLM exposure or stale docs of `subagent_spawn` and `audio_qa` outside the intended `agentctl subagent ...` and `agentctl media audio-qa ...` shell CLIs and guard tests.

## Success Criteria
- Active code/tests/docs are searched with `.complex-problems` excluded.
- Valid references inside CLI implementation and absence-guard tests are identified.
- Stale or misleading references are fixed if found.
- Current direct LLM tool schemas remain free of subagent/audio direct tools.

## Subproblems
- P023: Update vmuse long-running command guidance to shell-first contract
- P024: Reconcile current perception/action architecture doc with shell-first subagent/audio contract

## Results
- R010

## Latest Check
C017

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P015/children/P020/README.md
- Ticket T014: problems/P000/children/P001/children/P009/children/P015/children/P020/tickets/T014.md
- Result R010: problems/P000/children/P001/children/P009/children/P015/children/P020/results/R010.md
- Check C013: problems/P000/children/P001/children/P009/children/P015/children/P020/checks/C013.md
- Check C015: problems/P000/children/P001/children/P009/children/P015/children/P020/checks/C015.md
- Check C017: problems/P000/children/P001/children/P009/children/P015/children/P020/checks/C017.md

## Follow-ups
- P023: Update vmuse long-running command guidance to shell-first contract
- P024: Reconcile current perception/action architecture doc with shell-first subagent/audio contract
