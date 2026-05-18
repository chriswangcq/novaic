# P122: Artifact-Producing CLI Blob Manifest Contract Audit

Status: done
Parent: P104
Root: P000
Source Ticket: T116 (split)
Source Check: none
Package: problems/P000/children/P002/children/P104/children/P122
Body: problems/P000/children/P002/children/P104/children/P122/README.md
Ticket(s): T117

## Problem
Media-producing shell CLIs such as `devicectl hd screenshot` and file-pull paths must return bounded text plus `tool-output.v1` artifact manifests with `blob://runtime-artifact/...` refs, not raw bytes or base64 in stdout.

## Success Criteria
- Inspect artifact manifest helper and relevant shell capability CLI implementations.
- Verify screenshot/file-pull outputs contain `tool-output.v1` and blob artifact metadata.
- Verify raw base64 payloads are absent from stdout.
- Fix missing guards for any media CLI path found leaking raw bytes.

## Subproblems
- none

## Results
- R114

## Latest Check
C128

## Bodies
- Problem: problems/P000/children/P002/children/P104/children/P122/README.md
- Ticket T117: problems/P000/children/P002/children/P104/children/P122/tickets/T117.md
- Result R114: problems/P000/children/P002/children/P104/children/P122/results/R114.md
- Check C128: problems/P000/children/P002/children/P104/children/P122/checks/C128.md

## Follow-ups
- none
