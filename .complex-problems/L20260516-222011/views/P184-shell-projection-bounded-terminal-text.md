# P184: Shell projection bounded terminal text

Status: done
Parent: P127
Root: P000
Source Ticket: T174 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P184
Body: problems/P000/children/P003/children/P127/children/P184/README.md
Ticket(s): T175

## Problem
Shell output should look like terminal text to the LLM and monitor, with bounded/truncated public text and no hidden artifact/media payload injection. This contract must be audited at both Cortex projection and runtime shell wrapper boundaries.

## Success Criteria
- Map shell output projection functions and runtime shell wrapper behavior.
- Prove public shell text is bounded/truncated and terminal-style.
- Prove large shell output remains inspectable through durable step/payload refs rather than inline context.
- Fix or split any branch that emits unbounded shell text.

## Subproblems
- none

## Results
- R172

## Latest Check
C186

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P184/README.md
- Ticket T175: problems/P000/children/P003/children/P127/children/P184/tickets/T175.md
- Result R172: problems/P000/children/P003/children/P127/children/P184/results/R172.md
- Check C186: problems/P000/children/P003/children/P127/children/P184/checks/C186.md

## Follow-ups
- none
