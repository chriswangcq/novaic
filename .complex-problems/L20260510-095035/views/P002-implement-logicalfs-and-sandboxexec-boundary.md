# P002: Implement LogicalFS And SandboxExec Boundary

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
Create the production code boundary that separates filesystem semantics from process execution. The active code should have named components for LogicalFS view acquisition/release, generic process running, and shell orchestration.

## Success Criteria
- Introduce a LogicalFS provider abstraction for the current local mirror substrate.
- Introduce a SandboxExec/process runner that does not know Cortex store, RO/RW sync, or changed files.
- Introduce a ShellExecutionOrchestrator that composes LogicalFS and SandboxExec.
- Preserve capability scripts, token/API injection, timeout handling, path sanitization, and `ShellResult` shape.
- Add explicit RW convention environment variables for public/self/tmp/artifacts/scratch.

## Subproblems
- none

## Results
- R001

## Latest Check
C001

## Bodies
- Problem: problems/P000/children/P002/README.md
- Ticket T002: problems/P000/children/P002/tickets/T002.md
- Result R001: problems/P000/children/P002/results/R001.md
- Check C001: problems/P000/children/P002/checks/C001.md

## Follow-ups
- none
