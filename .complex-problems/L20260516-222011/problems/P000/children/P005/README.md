# LogicalFS sandbox blob layering audit

## Problem

Audit and optimize the current layering among Cortex, LogicalFS, sandbox service, sandbox core, and blob service. Ensure real-time RO/RW file semantics go through LogicalFS/sandbox as intended while cheap durable artifacts use blob, with no old direct materialization bypasses.

## Success Criteria

- Layer boundaries and current imports/calls are inspected.
- Direct fallback/backdoor paths are searched.
- Any stale fallback or misleading compatibility route is removed or documented as current necessity.
- Tests or static checks verify the intended layering where feasible.
