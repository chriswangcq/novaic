# P593: Current Display Image Injection Test Coverage

Status: done
Parent: P582
Root: P000
Source Ticket: T584 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P593
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P593/README.md
Ticket(s): T585

## Problem
Verify that current-round `display` tool results are covered by regression tests that prove BlobRef image references are resolved into provider image content for the active LLM call.

## Success Criteria
- Records exact `rg` scan commands and focused test commands for current display image injection.
- Cites the runtime tests that assert `display_perception` projection is selected for current display tool messages.
- Cites the runtime tests that assert BlobRef `image_ref` content is resolved to image MCP content for the provider call.
- Creates a concrete follow-up if this current-turn perception path lacks direct coverage.
- Explains why this belongs under the display regression inventory split.

## Subproblems
- none

## Results
- R579

## Latest Check
C617

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P593/README.md
- Ticket T585: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P593/tickets/T585.md
- Result R579: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P593/results/R579.md
- Check C617: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P593/checks/C617.md

## Follow-ups
- none
