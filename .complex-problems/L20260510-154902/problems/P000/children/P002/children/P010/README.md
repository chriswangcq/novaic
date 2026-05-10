# Phase 1.4: Verify substrate boundaries and non-integration

## Problem

Audit and test the Phase 1 substrate so it is usable by later phases without silently half-cutting over current Cortex behavior. This belongs under Phase 1 because the substrate must be proven independent, deterministic, and not a hidden dual-source integration.

## Success Criteria

- Focused ContextEvent tests pass.
- Relevant existing Cortex workspace/context tests pass after adding the substrate.
- Diff review confirms Phase 1 adds the substrate and tests, but does not silently route existing write/read endpoints through a partial event path.
- Static search confirms no new hidden `uuid`, wall-clock, environment, or direct legacy DFS fallback is introduced inside the domain logic.
- Phase 1 result records exact tests and residual integration gaps for P003-P006.
