# P580: Child Problem: Display tool implementation and blob/artifact contract

Status: done
Parent: P575
Root: P000
Source Ticket: T572 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/README.md
Ticket(s): T573

## Problem
Audit the display tool implementation and configuration to verify image/media artifacts are loaded from BlobRefs or equivalent stable artifact references, and that display's direct tool result is a concise acknowledgement rather than raw image/base64 text.

## Success Criteria
- Records scan commands for display tool definitions and handlers.
- Reads display implementation/configuration slices with line references.
- Classifies display return payloads as intended perception, bounded text, risky raw media, or follow-up.
- Forwards any raw base64/history residue to P554.

## Subproblems
- P584: Follow-up Problem: Replace display durable image bytes with BlobRef-backed perception fetch

## Results
- R568

## Latest Check
C615

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/README.md
- Ticket T573: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/tickets/T573.md
- Result R568: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/results/R568.md
- Check C604: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/checks/C604.md
- Check C615: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/checks/C615.md

## Follow-ups
- P584: Follow-up Problem: Replace display durable image bytes with BlobRef-backed perception fetch
