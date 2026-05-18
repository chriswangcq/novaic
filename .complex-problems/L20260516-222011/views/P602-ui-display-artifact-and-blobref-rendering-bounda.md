# P602: UI Display Artifact and BlobRef Rendering Boundary

Status: done
Parent: P583
Root: P000
Source Ticket: T592 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P602
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P602/README.md
Ticket(s): T603

## Problem
Audit UI handling of display artifacts and BlobRefs to verify images are shown through artifact/display paths rather than by rendering raw base64 tool text.

## Success Criteria
- Records exact scans for BlobRef, artifact, image, thumbnail, and display rendering in frontend code.
- Cites UI slices that show BlobRef/artifact rendering behavior.
- Classifies any base64 rendering as either intentional provider request debug or risky UI residue.
- Creates a follow-up if UI display requires raw base64 from tool text.

## Subproblems
- P611: UI Chat Attachment BlobRef Rendering
- P612: UI Monitor and Log Artifact Display Boundary
- P613: UI Base64 Residue Classification

## Results
- R600

## Latest Check
C641

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P602/README.md
- Ticket T603: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P602/tickets/T603.md
- Result R600: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P602/results/R600.md
- Check C641: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P602/checks/C641.md

## Follow-ups
- none
