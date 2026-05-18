# P575: Display Tool Perception Contract Inventory

Status: done
Parent: P564
Root: P000
Source Ticket: T568 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/README.md
Ticket(s): T572

## Problem
Audit display tool handling to verify image/media outputs are delivered through the intended current-turn perception path and are not stored as raw base64 text in durable tool history or shell-visible output. This belongs under P564 because display is the primary boundary where media should become model-visible without becoming text payload residue.

## Success Criteria
- Records exact scan commands and outputs for display tool implementations, display result adapters, media payload handling, and tests.
- Reads relevant display/perception code/test slices with line references.
- Classifies display outputs as intended current-turn perception, risky history projection, removable compatibility path, or follow-up.
- Identifies whether display returns only bounded textual acknowledgements in normal tool history.
- Captures any high-confidence risky residue for P554 remediation.

## Subproblems
- P580: Child Problem: Display tool implementation and blob/artifact contract
- P581: Child Problem: Cortex display step-result projection contract
- P582: Child Problem: Display history and perception regression test inventory
- P583: Child Problem: Display monitor/UI projection boundary inventory

## Results
- R602

## Latest Check
C643

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/README.md
- Ticket T572: problems/P000/children/P005/children/P553/children/P564/children/P575/tickets/T572.md
- Result R602: problems/P000/children/P005/children/P553/children/P564/children/P575/results/R602.md
- Check C643: problems/P000/children/P005/children/P553/children/P564/children/P575/checks/C643.md

## Follow-ups
- none
