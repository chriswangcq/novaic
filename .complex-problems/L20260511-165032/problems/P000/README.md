# Audit unintegrated adapter paths after infrastructure cutovers

## Problem

Recent production debugging showed that the LogicalFS substrate had been improved, but the Cortex shell adapter still materialized old broad `/ro` paths. We need comprehensively audit the repository for similar gaps where a new infrastructure layer exists but an entrypoint, adapter, worker, or compatibility branch still uses an old direct path, broad scan, fallback, or hidden integration.

## Success Criteria

- Identify high-risk patterns similar to the shell LogicalFS miss: full recursive scans, old direct write/read paths, bypassed FSM/outbox decisions, broad fallback paths, and unused compatibility branches.
- Cover Cortex/LogicalFS/Sandbox, Agent Runtime Queue/FSM/Saga, shell capability tools, and deployment/worker wiring.
- Distinguish confirmed live-path gaps from tests/docs-only residue.
- Produce a concrete prioritized list of issues to fix or confidently report no issue, with evidence pointers.
- Validate the ledger and render the dashboard when the audit closes.
