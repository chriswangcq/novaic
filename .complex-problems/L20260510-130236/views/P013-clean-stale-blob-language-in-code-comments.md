# P013: Clean Stale Blob Language In Code Comments

Status: done
Parent: P008
Root: P000
Package: problems/P000/children/P004/children/P008/children/P013
Body: problems/P000/children/P004/children/P008/children/P013/README.md
Ticket(s): T011

## Problem
Code docstrings and comments still imply that Workspace/Store production semantics are Blob-backed. These comments sit near active constructors and are likely to mislead future code changes.

This child belongs under T010 because code-adjacent language should be cleaned before broader docs.

## Success Criteria
- `WorkspaceRegistry` comments/docstrings no longer describe live Workspace as Blob-backed authority.
- `CortexStore` / `LocalFileStore` comments no longer claim production live Workspace uses `BlobCortexStore` as the semantic authority.
- Workspace authority comments consistently point to LogicalFS/Cortex file authority for live `RO` / `RW`.
- Transitional adapter comments remain precise and local to `blob_store.py` / registry construction.

## Subproblems
- none

## Results
- R008

## Latest Check
C008

## Bodies
- Problem: problems/P000/children/P004/children/P008/children/P013/README.md
- Ticket T011: problems/P000/children/P004/children/P008/children/P013/tickets/T011.md
- Result R008: problems/P000/children/P004/children/P008/children/P013/results/R008.md
- Check C008: problems/P000/children/P004/children/P008/children/P013/checks/C008.md

## Follow-ups
- none
