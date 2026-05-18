# P577: Legacy Base64 And Multimodal Compatibility Residue Inventory

Status: done
Parent: P564
Root: P000
Source Ticket: T568 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P577
Body: problems/P000/children/P005/children/P553/children/P564/children/P577/README.md
Ticket(s): T611

## Problem
Search for stale base64, screenshot, data URI, image_url, multimodal compatibility, and provider adapter branches that may bypass the current artifact/display contract. This belongs under P564 because old compatibility paths can silently reintroduce raw media text even after the primary shell/display path is fixed.

## Success Criteria
- Records exact scan commands and outputs for base64/data URI/image_url/multimodal/provider compatibility terms.
- Reads relevant code/test slices with line references.
- Classifies hits as intended provider API formatting, risky raw-history injection, removable old compatibility, or follow-up.
- Identifies whether any legacy branch is still reachable from active runtime/tool paths.
- Captures any high-confidence risky residue for P554 remediation.

## Subproblems
- P617: Provider Adapter Multimodal Boundary Residue
- P618: Runtime and Cortex Multimodal Compatibility Residue
- P619: UI and Test Multimodal Residue Classification

## Results
- R610

## Latest Check
C651

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P577/README.md
- Ticket T611: problems/P000/children/P005/children/P553/children/P564/children/P577/tickets/T611.md
- Result R610: problems/P000/children/P005/children/P553/children/P564/children/P577/results/R610.md
- Check C651: problems/P000/children/P005/children/P553/children/P564/children/P577/checks/C651.md

## Follow-ups
- none
