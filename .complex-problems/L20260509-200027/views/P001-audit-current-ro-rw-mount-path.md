# P001: Audit Current RO/RW Mount Path

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
Establish the current facts: how shell execution creates temporary RO/RW directories, how it decides whether RO is needed, how it copies data, how it persists RW, and where repeated per-command work lives.

## Success Criteria
- Identify the exact code path from Runtime shell tool to Cortex shell execution.
- Explain RO/RW materialization and RW persistence mechanics.
- List confirmed bottlenecks and current mitigations with code references.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/children/P001/README.md
- Ticket T001: problems/P000/children/P001/tickets/T001.md
- Result R000: problems/P000/children/P001/results/R000.md
- Check C000: problems/P000/children/P001/checks/C000.md

## Follow-ups
- none
