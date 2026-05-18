# Ticket: Clean Cortex archive and diagnostic residue

## Goal

Audit and clean Cortex archive/direct scope-end diagnostic residue that was explicitly left outside the ContextEvent lifecycle branch.

## Acceptance Criteria

- Archive/direct scope-end paths are inventoried.
- Any live legacy/direct archive diagnostic bypass is either removed, routed through the intended lifecycle contract, or split into a precise child ticket.
- Tests or guards prove the resulting archive/diagnostic path is explicit and not silently mixed with ContextEvent projection logic.
