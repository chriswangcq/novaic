# Runtime finalize handler inventory check

## Summary

Success. The inventory found the expected paths and, importantly, surfaced additional mutation risks beyond the originally obvious session-ended handler: Cortex scope archive/notification processing and subagent status flips. Those are assigned to P350 rather than ignored.

## Evidence

- R331 lists live paths in wake-finalize saga, cortex handlers, subagent handlers, session handler, react contracts, saga compensation, and recovery archive shaping.
- R331 classifies mutation types:
  - Cortex archive and notification processed transition.
  - Business subagent sleeping/completed status changes.
  - Queue session-ended repository delivery.
  - Recovery/compensation-generated finalize/archive effects.
- R331 assigns implementation targets to P349-P352.

## Criteria Map

- List live handler/contract files and functions: satisfied.
- Mark each path as mutating or non-mutating: satisfied.
- Identify required identity fields for mutating paths: satisfied at inventory level; missing fields are called out.
- Produce implementation targets for remaining P337 children: satisfied.

## Execution Map

- Read-only source audit with `rg` and `nl`.
- No implementation done in P348.
- The inventory guides P349/P350/P351/P352.

## Stress Test

- Checked for a subtle non-session path: stale wake-finalize can still call subagent sleeping/completed and Cortex scope-end even if session-ended is protected. R331 catches this rather than falsely declaring runtime enforcement done.

## Residual Risk

- The risks remain open until P349-P352 are solved.

## Result IDs

- R331
