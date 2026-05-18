# P611: UI Chat Attachment BlobRef Rendering

Status: done
Parent: P602
Root: P000
Source Ticket: T603 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P602/children/P611
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P602/children/P611/README.md
Ticket(s): T604

## Problem
Audit chat and application attachment rendering/conversion to ensure uploaded or runtime image attachments are rendered from BlobRef/authenticated URLs and never require raw base64 tool text in normal UI paths.

## Success Criteria
- Records exact scans for chat attachment, BlobRef, image preview, data URL, and base64 paths.
- Cites UI slices for `FileAttachment`, image preview overlay, and application attachment conversion.
- Runs focused tests for attachment conversion/path behavior.
- Creates a follow-up if chat attachment rendering depends on raw base64 tool text.

## Subproblems
- none

## Results
- R597

## Latest Check
C638

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P602/children/P611/README.md
- Ticket T604: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P602/children/P611/tickets/T604.md
- Result R597: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P602/children/P611/results/R597.md
- Check C638: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P602/children/P611/checks/C638.md

## Follow-ups
- none
