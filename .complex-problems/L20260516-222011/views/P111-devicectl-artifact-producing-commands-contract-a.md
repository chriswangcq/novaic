# P111: Devicectl Artifact-Producing Commands Contract Audit

Status: done
Parent: P106
Root: P000
Source Ticket: T103 (split)
Source Check: none
Package: problems/P000/children/P002/children/P103/children/P106/children/P111
Body: problems/P000/children/P002/children/P103/children/P106/children/P111/README.md
Ticket(s): T104

## Problem
`devicectl hd screenshot` and `devicectl hd file-pull` produce media/file payloads and must upload to Blob Service and print `tool-output.v1` artifact manifests, not inline base64/data fields.

## Success Criteria
- Inspect artifact-producing devicectl implementation.
- Verify screenshot and file-pull upload to blob and omit base64/raw data from stdout.
- Run focused fake-server tests for artifact contract.
- Fix bounded gaps found.

## Subproblems
- none

## Results
- R100

## Latest Check
C114

## Bodies
- Problem: problems/P000/children/P002/children/P103/children/P106/children/P111/README.md
- Ticket T104: problems/P000/children/P002/children/P103/children/P106/children/P111/tickets/T104.md
- Result R100: problems/P000/children/P002/children/P103/children/P106/children/P111/results/R100.md
- Check C114: problems/P000/children/P002/children/P103/children/P106/children/P111/checks/C114.md

## Follow-ups
- none
