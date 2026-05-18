# P806: Packaged Blob Binary Contract Remediation

Status: done
Parent: P805
Root: P000
Source Ticket: T796 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P806
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P806/README.md
Ticket(s): T797

## Problem
The packaged backend startup scripts look for `novaic-blob-service`, but the generated packaged backend assets contain `novaic-storage-a` and the source resource backend directory contains no blob binary. This makes packaged startup behavior depend on a binary name/path that does not match committed assets.

## Success Criteria
- Active packaged startup scripts start the actual committed blob/storage binary name or clearly fail with an explicit diagnostic when the binary is absent.
- Source resource and generated backend asset copies no longer disagree about the intended blob/storage binary contract.
- Targeted scans for `novaic-blob-service`, `novaic-storage-a`, and blob service startup paths show only intentional references.
- `bash -n` passes for the modified packaged startup scripts.

## Subproblems
- P810: Resource Storage Binary Source Boundary

## Results
- R786

## Latest Check
C835

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P806/README.md
- Ticket T797: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P806/tickets/T797.md
- Result R786: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P806/results/R786.md
- Check C833: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P806/checks/C833.md
- Check C835: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P806/checks/C835.md

## Follow-ups
- P810: Resource Storage Binary Source Boundary
