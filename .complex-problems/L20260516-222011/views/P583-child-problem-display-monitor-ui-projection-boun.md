# P583: Child Problem: Display monitor/UI projection boundary inventory

Status: done
Parent: P575
Root: P000
Source Ticket: T572 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/README.md
Ticket(s): T592

## Problem
Audit monitor/log UI and factory-log rendering paths that show display/tool results to humans, ensuring UI truncation or thumbnails do not imply that raw media bytes are part of the LLM text context.

## Success Criteria
- Records scan commands for monitor, factory logs, and display-related UI rendering.
- Reads relevant UI/log rendering slices with line references.
- Separates human UI preview/truncation from LLM request context.
- Forwards any UI path that stores or displays unredacted raw image bytes as a risky residue.

## Subproblems
- P600: Factory Log Request Context and Raw JSON Boundary
- P601: Agent Monitor Step Preview Boundary
- P602: UI Display Artifact and BlobRef Rendering Boundary

## Results
- R601

## Latest Check
C642

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/README.md
- Ticket T592: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/tickets/T592.md
- Result R601: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/results/R601.md
- Check C642: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/checks/C642.md

## Follow-ups
- none
