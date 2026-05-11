# P001: Inventory shell CLI surfaces and blob-contract risks

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
Before changing behavior, inventory every shell-exposed CLI command surface and classify which commands produce plain text, structured JSON, files, media, screenshots, or potentially large payloads. Identify live paths that can violate the blob artifact contract.

## Success Criteria
- `agentctl`, `cortex`, and `devicectl` shell capability command surfaces are inventoried.
- Each command is classified as text-only, structured-small, payload-inspection, file/media-producing, or proxy/raw.
- Confirmed blob-contract risks are listed with exact code pointers.
- The next repair targets are clear and bounded.

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
