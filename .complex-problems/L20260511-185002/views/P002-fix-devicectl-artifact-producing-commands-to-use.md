# P002: Fix devicectl artifact-producing commands to use blob contract

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
`devicectl hd screenshot` currently returns a raw proxy result that can contain inline base64 image data in shell stdout. This violates the `tool-output.v1` artifact contract and causes huge stdout previews/context payloads. Other `devicectl hd` file/media-producing commands must also be checked and fixed if they emit raw file data.

## Success Criteria
- `devicectl hd screenshot` returns bounded `tool-output.v1` JSON with image artifact metadata and a `blob://...` URI.
- Raw screenshot base64 is not printed as primary stdout text.
- Any touched device/file commands follow the same artifact convention or are documented as non-artifact commands.
- Tests cover the transformed screenshot output.

## Subproblems
- none

## Results
- R001

## Latest Check
C001

## Bodies
- Problem: problems/P000/children/P002/README.md
- Ticket T002: problems/P000/children/P002/tickets/T002.md
- Result R001: problems/P000/children/P002/results/R001.md
- Check C001: problems/P000/children/P002/checks/C001.md

## Follow-ups
- none
