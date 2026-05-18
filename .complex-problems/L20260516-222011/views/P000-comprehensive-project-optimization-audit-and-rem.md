# P000: Comprehensive project optimization audit and remediation

Status: done
Parent: none
Root: P000
Source Ticket: none (none)
Source Check: none
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
The project has gone through many architecture migrations around agent runtime, queue FSM, Cortex context assembly, shell CLI contraction, display/blob projection, LogicalFS, sandbox-service, and operational state ownership. The user wants a comprehensive review of optimizable points and wants discovered issues optimized, with strict recursive ledger discipline rather than a broad one-go pass.

This work must audit the current multi-repository workspace, find high-value correctness, boundary, cleanup, contract, test, and maintainability issues, implement safe fixes, remove misleading residue where appropriate, and verify the results with targeted and project-level checks. Because broad "optimize everything" is high-risk, the root must split into multiple child problems before any one-go execution.

## Success Criteria
- A new schema-v6 ledger exists for this audit, with explicit tickets, results, checks, and follow-ups for discovered gaps.
- The audit is split into enough independent child problems before one-go is considered; shallow one-go shortcuts are avoided.
- Current architecture contracts are inspected across runtime, Cortex, shell CLI/tool-output, LogicalFS/sandbox service boundaries, tests, docs, and deployment-facing configuration.
- Discovered high-confidence optimizations are implemented rather than merely listed, unless explicitly blocked or unsafe.
- Any code changes prefer deletion or simplification of residue over additive compatibility branches, consistent with AI-era programming principles.
- Verification includes focused tests for touched components, a diff/stat review, and residual-risk notes.
- The final answer reports what was audited, what was changed, what was verified, and what risk remains.

## Subproblems
- P001: Repo topology and residue inventory
- P002: Shell tool contract and CLI usability audit
- P003: Cortex context projection and payload boundary audit
- P004: Queue FSM session and worker boundary audit
- P005: LogicalFS sandbox blob layering audit
- P006: Tests docs and architecture guard audit
- P007: Deployment runtime observability and smoke audit

## Results
- R834

## Latest Check
C883

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R834: problems/P000/results/R834.md
- Check C883: problems/P000/checks/C883.md

## Follow-ups
- none
