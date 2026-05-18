# P564: Runtime Display Tool Output Projection Residue Inventory

Status: done
Parent: P553
Root: P000
Source Ticket: T557 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564
Body: problems/P000/children/P005/children/P553/children/P564/README.md
Ticket(s): T568

## Problem
Search agent-runtime and Cortex projection code for stale base64, display, artifact, payload, and multimodal compatibility paths that could put media bytes into public shell/history context or bypass the current `tool-output.v1` manifest contract. This belongs under P553 because shell/display contract regressions were a recent failure mode.

## Success Criteria
- Records exact static scan commands and outputs.
- Classifies base64/display/artifact/tool-output hits as intended, risky, removable, or follow-up.
- Separates valid current-turn `display_perception` image delivery from invalid historical/shell image injection.
- Captures any high-confidence risky residue for P554 remediation.

## Subproblems
- P574: Runtime LLM Request Projection Path Inventory
- P575: Display Tool Perception Contract Inventory
- P576: Shell History Tool Output Contract Inventory
- P577: Legacy Base64 And Multimodal Compatibility Residue Inventory

## Results
- R611

## Latest Check
C652

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/README.md
- Ticket T568: problems/P000/children/P005/children/P553/children/P564/tickets/T568.md
- Result R611: problems/P000/children/P005/children/P553/children/P564/results/R611.md
- Check C652: problems/P000/children/P005/children/P553/children/P564/checks/C652.md

## Follow-ups
- none
