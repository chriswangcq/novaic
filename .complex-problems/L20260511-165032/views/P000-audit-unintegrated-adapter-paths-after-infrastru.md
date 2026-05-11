# P000: Audit unintegrated adapter paths after infrastructure cutovers

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Recent production debugging showed that the LogicalFS substrate had been improved, but the Cortex shell adapter still materialized old broad `/ro` paths. We need comprehensively audit the repository for similar gaps where a new infrastructure layer exists but an entrypoint, adapter, worker, or compatibility branch still uses an old direct path, broad scan, fallback, or hidden integration.

## Success Criteria
- Identify high-risk patterns similar to the shell LogicalFS miss: full recursive scans, old direct write/read paths, bypassed FSM/outbox decisions, broad fallback paths, and unused compatibility branches.
- Cover Cortex/LogicalFS/Sandbox, Agent Runtime Queue/FSM/Saga, shell capability tools, and deployment/worker wiring.
- Distinguish confirmed live-path gaps from tests/docs-only residue.
- Produce a concrete prioritized list of issues to fix or confidently report no issue, with evidence pointers.
- Validate the ledger and render the dashboard when the audit closes.

## Subproblems
- P001: Audit Cortex LogicalFS and Sandbox adapter cutover
- P002: Audit Queue FSM Saga and session adapter cutover
- P003: Audit shell capability and tool CLI migration
- P004: Audit Cortex context event source cutover
- P005: Audit deployment process and compatibility residue

## Results
- R005

## Latest Check
C005

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R005: problems/P000/results/R005.md
- Check C005: problems/P000/checks/C005.md

## Follow-ups
- none
