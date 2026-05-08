# Pure DSL Architecture Status Documentation

## Problem

The codebase needs durable documentation of the actual architecture after optimization: what is pure/spec-driven, what remains as accepted computation hooks, and what guards prevent old paths from returning.

## Success Criteria

- Add or update an architecture/design note describing the implemented FSM/worker/DSL shape.
- The note references the live roster/FSM path, plan-first effect boundary, assembly specs, handler metadata, and explicit accepted non-DSL computation hooks.
- Stale wording that claims premature pure DSL completion is not present.
- Documentation is included in final verification and ledger closure.
