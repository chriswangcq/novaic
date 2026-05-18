# P104: Blob Artifact and Display Contract Audit

Status: done
Parent: P002
Root: P000
Source Ticket: T096 (split)
Source Check: none
Package: problems/P000/children/P002/children/P104
Body: problems/P000/children/P002/children/P104/README.md
Ticket(s): T116

## Problem
CLI tools that produce media or large outputs should return text plus artifact manifests, with display consuming blob refs without reinserting raw base64 into context.

## Success Criteria
- Inspect artifact manifest helpers and display projection tests.
- Verify screenshot/media CLI returns blob artifacts rather than base64 text.
- Verify display/tool history projection remains sanitized.
- Fix or route any contract gap.

## Subproblems
- P122: Artifact-Producing CLI Blob Manifest Contract Audit
- P123: Display Tool History Sanitization Audit
- P124: Provider-Native Image Projection Audit
- P125: Blob Artifact and Display Base64 Regression Sweep

## Results
- R118

## Latest Check
C132

## Bodies
- Problem: problems/P000/children/P002/children/P104/README.md
- Ticket T116: problems/P000/children/P002/children/P104/tickets/T116.md
- Result R118: problems/P000/children/P002/children/P104/results/R118.md
- Check C132: problems/P000/children/P002/children/P104/checks/C132.md

## Follow-ups
- none
