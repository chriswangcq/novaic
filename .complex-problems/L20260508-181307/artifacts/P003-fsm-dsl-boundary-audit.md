# FSM Worker DSL Boundary Audit

## Problem

Audit whether the implemented runtime shape matches the documented FSM/worker/DSL architecture: generic FSM substrate, generic worker substrate, declarative roster/assembly specs, pure policy/spec/plan helpers, plan-first effects, and explicit accepted Python computation hooks.

## Success Criteria

- The live code paths named in `runtime-fsm-worker-dsl-status.md` exist and are imported/used consistently.
- The audit verifies action engines delegate behavior calculation to policy/spec/plan helpers where claimed.
- Accepted Python computation hooks are explicitly named and are not hidden fallback paths.
- Any mismatch between documentation and implementation is fixed or converted into a follow-up problem.
