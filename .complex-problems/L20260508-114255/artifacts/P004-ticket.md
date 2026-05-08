## Ticket: Audit Verification Guardrails And Docs Alignment

### Problem Definition

Audit whether tests, residue guards, and architecture documents adequately protect the intended FSM substrate plus business DSL architecture from regression, stale docs, and silent old-path reintroduction.

### Proposed Solution

Inspect relevant tests and architecture documents for coverage of generic FSM substrate, worker substrate, handler thinness, old-path deletion, runtime wiring, and business DSL gaps. Run a representative targeted test set. Identify missing guardrails.

### Acceptance Criteria

- Confirm which invariants are currently protected by tests.
- Confirm whether docs describe the current shape and remaining gap accurately.
- Identify guardrail gaps around action-engine declarativity, assembly thickness, deployment supervision, and stale operational evidence.
- Produce evidence-based recommendation list without modifying code.

### Verification Plan

- Use `find`, `rg`, and `nl` over tests and docs.
- Run targeted tests for generic FSM/worker substrate, worker registry, residue guards, and business handler lifecycle boundaries.
- Compare docs against code findings from P001-P003.

### Risks

- A passing targeted suite does not prove the whole repository is green; this ticket is an audit, not a full CI run.
- Existing docs may intentionally be design ledgers rather than current reference docs; call that out if found.

### Assumptions

- No code changes are required for this audit ticket.
- Documentation can include aspirational future-state sections, but current-state claims must not be misleading.
