# P595: Durable Shell and Display Output Base64 Absence Test Coverage

Status: done
Parent: P582
Root: P000
Source Ticket: T584 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P595
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P595/README.md
Ticket(s): T587

## Problem
Verify that durable shell/display output tests protect the contract that large visual payloads are represented by BlobRef manifests rather than raw base64 text in durable tool results.

## Success Criteria
- Records exact scans for base64/data-url assertions in shell, display, tool handler, and Cortex projection tests.
- Cites tests proving `devicectl hd screenshot` or equivalent shell-visible screenshot output returns a BlobRef artifact manifest.
- Cites tests proving `display` durable payload stores `image_ref` or display file metadata without inline `data`.
- Creates a concrete follow-up if durable base64 absence is not directly tested.
- Explains why this belongs under the display regression inventory split.

## Subproblems
- P597: Shell Screenshot CLI BlobRef Manifest Test Coverage
- P598: Display Handler Durable ImageRef Test Coverage
- P599: Cortex Projection BlobRef No-Inline Test Coverage

## Results
- R584

## Latest Check
C622

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P595/README.md
- Ticket T587: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P595/tickets/T587.md
- Result R584: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P595/results/R584.md
- Check C622: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P595/checks/C622.md

## Follow-ups
- none
