# Phase 5A Residue Audit And Classification

## Problem

Before deleting cleanup residue, we need a high-quality audit that distinguishes live current-code/current-doc residue from historical ledger/audit artifacts. Without this classification, cleanup can either miss live old paths or delete useful historical evidence.

## Success Criteria

- Audit code, tests, and current docs for local NDJSON transition authority, active-stack file walking, temp backing path authority, process-local fallback state, and compatibility branches.
- Classify every hit as live residue to remove, current wording to update, test guard target, or historical evidence to keep.
- Produce a concrete removal/guard target list for later Phase 5 children.
- Do not perform deletion in this child; this child is audit-only.
