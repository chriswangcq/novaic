# P234: Audit large shell/display output projection boundary

Status: done
Parent: P229
Root: P000
Source Ticket: T222 (split)
Source Check: none
Package: problems/P000/children/P003/children/P129/children/P229/children/P234
Body: problems/P000/children/P003/children/P129/children/P229/children/P234/README.md
Ticket(s): T230

## Problem
Large shell stdout, CLI artifact manifests, and display/image outputs must remain compact in model-visible text. Any raw base64 or large stdout should be behind durable payload or explicit artifact/display handling, not normal history text.

This belongs under `P229` because shell/display were the concrete regression class that previously put huge/base64 data into context.

## Success Criteria
- Shell result projection and display/media result projection paths are mapped with file/function pointers.
- Evidence shows large/base64 output is truncated or replaced with manifest/projection text in normal context.
- Focused tests pass for shell output truncation, artifact manifest handling, display media handling, and no historical tool image/base64 injection.

## Subproblems
- none

## Results
- R226

## Latest Check
C240

## Bodies
- Problem: problems/P000/children/P003/children/P129/children/P229/children/P234/README.md
- Ticket T230: problems/P000/children/P003/children/P129/children/P229/children/P234/tickets/T230.md
- Result R226: problems/P000/children/P003/children/P129/children/P229/children/P234/results/R226.md
- Check C240: problems/P000/children/P003/children/P129/children/P229/children/P234/checks/C240.md

## Follow-ups
- none
