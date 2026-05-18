# Queue FSM session and worker boundary audit

## Problem

Audit and optimize queue service/session runtime boundaries after the FSM migration: session state SSOT, outbox behavior, worker assembly, old imperative dispatch branches, finalize ownership, and generation checks.

## Success Criteria

- Current queue/FSM entry points and worker roles are mapped.
- Residual active direct-path branches or compatibility shims are identified.
- High-confidence residue is removed or tightened behind explicit tests.
- Focused tests cover dispatch/session/finalize behavior impacted by any changes.
