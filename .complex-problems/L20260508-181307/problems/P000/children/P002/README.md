# Old Path And Compatibility Residue Scan

## Problem

Audit the runtime worker/action/handler source surface for old paths that could bypass the new FSM/worker/DSL boundaries: direct effect execution in action engines, handler-owned lifecycle wiring, bespoke worker loops, compatibility branches, or stale no-generation/fallback behavior.

## Success Criteria

- Source scans cover action engines, handlers, worker assemblies, worker entrypoints, and Queue Service session/FSM surfaces.
- Findings distinguish accepted explicit boundaries from active old-path residue.
- No direct action-engine `execute_effect(...)`, handler lifecycle ownership, or displaced bespoke loop remains unguarded.
- Any real residue is fixed or converted into a follow-up problem.
