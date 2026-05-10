# P000: Implement LogicalFS RO/RW authority boundary end to end

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Implement the architecture documented in `docs/architecture/logicalfs-realtime-file-authority.md` across the repository. The target boundary is narrow and strict:

- LogicalFS is the only live Cortex/shell `RO` / `RW` file authority.
- Blob remains a cheap byte/object file server for attachments, display bytes, artifact bytes, downloads, and LogicalFS persistence internals.
- Cortex owns scope/workspace semantics but must use LogicalFS for live file operations.
- Sandboxd owns process execution but must not own workspace, subagent, or file persistence semantics.
- Display/download must go through Blob; LogicalFS must not expose display/download handles.

This implementation must avoid the previous failure mode where new code exists but active paths continue to use old logic. Existing user work and historical ledgers must not be reverted.

## Success Criteria
- Repository active shell path uses LogicalFS and sandboxd for Cortex/shell `RO` / `RW` execution, with tests proving the active path.
- No non-LogicalFS live `RO` / `RW` path remains in Cortex, Runtime, or Sandbox code.
- Direct Blob object APIs remain allowed only for cheap byte serving or LogicalFS persistence internals, not live Cortex/shell file semantics.
- Sandboxd service has no Cortex workspace/subagent semantics beyond executing a provided filesystem view.
- Tests/guardrails catch future direct live `RO` / `RW` bypasses.
- Deployment/service scripts include the final service topology and do not reference removed legacy packages or fallback paths.
- Ledger records tickets, results, checks, residual risks, and follow-up closure.

## Subproblems
- P001: Audit current live RO/RW active paths
- P002: Cut Cortex live RO/RW operations behind LogicalFS
- P003: Enforce sandboxd as process-only execution boundary
- P004: Clean Blob boundary and live RO/RW bypasses
- P005: Final verification, cleanup, and deployment readiness
- P019: Replace In-Process Cortex File Authority With LogicalFS Boundary
- P036: Fix Canonical Test Matrix LogicalFS Dependency Boundary

## Results
- R018

## Latest Check
C038

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R018: problems/P000/results/R018.md
- Check C018: problems/P000/checks/C018.md
- Check C036: problems/P000/checks/C036.md
- Check C038: problems/P000/checks/C038.md

## Follow-ups
- P019: Replace In-Process Cortex File Authority With LogicalFS Boundary
- P036: Fix Canonical Test Matrix LogicalFS Dependency Boundary
