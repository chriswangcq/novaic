# P023: Update vmuse long-running command guidance to shell-first contract

Status: done
Parent: P020
Root: P000
Source Ticket: none (none)
Source Check: C013
Package: problems/P000/children/P001/children/P009/children/P015/children/P020/children/P023
Body: problems/P000/children/P001/children/P009/children/P015/children/P020/children/P023/README.md
Ticket(s): T015

## Problem
The vmuse shell tool documentation and bundled app resource copies still instruct agents to use direct `subagent_spawn(...)` for long-running commands. Update the guidance to avoid direct-tool assumptions and prefer the current NovaIC shell CLI form where available.

## Success Criteria
- Source vmuse guidance no longer recommends direct `subagent_spawn(...)` syntax.
- Bundled app resource copies are updated consistently.
- Timeout warning text avoids direct-tool syntax.
- Focused search confirms no current vmuse source/resource direct `subagent_spawn(...)` guidance remains.

## Subproblems
- none

## Results
- R011

## Latest Check
C014

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P015/children/P020/children/P023/README.md
- Ticket T015: problems/P000/children/P001/children/P009/children/P015/children/P020/children/P023/tickets/T015.md
- Result R011: problems/P000/children/P001/children/P009/children/P015/children/P020/children/P023/results/R011.md
- Check C014: problems/P000/children/P001/children/P009/children/P015/children/P020/children/P023/checks/C014.md

## Follow-ups
- none
