# P002: Shell tool contract and CLI usability audit

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T096

## Problem
Audit and optimize the current shell-first tool model: LLM-visible tool count, shell output truncation, `desc`, `agentctl`, `devicectl`, `cortex` CLI coverage, blob artifact contracts, and hidden direct-tool residue.

## Success Criteria
- Shell contract implementation and tests are inspected.
- CLI help/dispatch coverage is checked for current intended capabilities.
- Any direct-tool residue or misleading old paths are removed or made unreachable with tests.
- Targeted tests verify shell output and CLI contract behavior.

## Subproblems
- P102: Shell Output and Desc Contract Audit
- P103: Agentctl Devicectl Cortex CLI Coverage Audit
- P104: Blob Artifact and Display Contract Audit

## Results
- R119

## Latest Check
C133

## Bodies
- Problem: problems/P000/children/P002/README.md
- Ticket T096: problems/P000/children/P002/tickets/T096.md
- Result R119: problems/P000/children/P002/results/R119.md
- Check C133: problems/P000/children/P002/checks/C133.md

## Follow-ups
- none
