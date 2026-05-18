# P632: LogicalFS Sandbox Fallback Remediation Guard

Status: done
Parent: P554
Root: P000
Source Ticket: T626 (split)
Source Check: none
Package: problems/P000/children/P005/children/P554/children/P632
Body: problems/P000/children/P005/children/P554/children/P632/README.md
Ticket(s): T642

## Problem
After removing stale materialization/scratch residue, the codebase needs a final skeptical guard pass so future changes do not reintroduce local materialization, old sandbox temp paths, Blob-as-workspace semantics, or runtime-local shell fallback.

## Success Criteria
- Runs targeted static scans for `materialize`, `novaic-cortex-sandbox`, `/tmp/novaic-cortex-sandbox`, `/rw/scratch`, local shell fallback, and direct Blob workspace authority terms.
- Runs focused Cortex LogicalFS/workspace/sandbox boundary tests.
- Documents any remaining hits as intended, removed, or follow-up-worthy.
- Creates a follow-up if any risky active residue remains.

## Subproblems
- P646: LogicalFS Materialization Residue Audit
- P647: Sandbox Backing Path Residue Audit
- P648: Runtime Local Shell Fallback Residue Audit
- P649: Blob Workspace Authority Residue Audit
- P650: LogicalFS Sandbox Boundary Focused Verification

## Results
- R649

## Latest Check
C691

## Bodies
- Problem: problems/P000/children/P005/children/P554/children/P632/README.md
- Ticket T642: problems/P000/children/P005/children/P554/children/P632/tickets/T642.md
- Result R649: problems/P000/children/P005/children/P554/children/P632/results/R649.md
- Check C691: problems/P000/children/P005/children/P554/children/P632/checks/C691.md

## Follow-ups
- none
