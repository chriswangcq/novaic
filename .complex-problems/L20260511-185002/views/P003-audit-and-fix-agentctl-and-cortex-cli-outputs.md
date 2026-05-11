# P003: Audit and fix agentctl and cortex CLI outputs

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T003

## Problem
`agentctl` and `cortex` are shell-exposed CLIs. They need to be checked for commands that return large payloads, file contents, binary data, or embedded blob contents through stdout instead of returning references or bounded text.

## Success Criteria
- `agentctl` command surface is inspected for blob-contract violations.
- `cortex` command surface is inspected for blob-contract violations.
- Any confirmed live violation is fixed or split into a follow-up if it is a distinct large repair.
- Text/payload-inspection commands remain bounded and explicit.

## Subproblems
- P005: Audit and fix agentctl CLI Blob contract
- P006: Audit and fix cortex CLI Blob contract

## Results
- R004

## Latest Check
C004

## Bodies
- Problem: problems/P000/children/P003/README.md
- Ticket T003: problems/P000/children/P003/tickets/T003.md
- Result R004: problems/P000/children/P003/results/R004.md
- Check C004: problems/P000/children/P003/checks/C004.md

## Follow-ups
- none
