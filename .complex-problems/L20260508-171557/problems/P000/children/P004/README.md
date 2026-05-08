# Saga Launch And Definition Plan Boundary

## Problem

Saga launch still publishes tasks and marks state in a direct loop, while saga definitions are DSL-like but callback-heavy. Introduce a deterministic saga launch plan boundary and clarify callback extension points.

## Success Criteria

- Saga launch can produce an explicit plan from saga state, definition, and context.
- Saga launch engine executes through the generic plan/effect substrate.
- Saga definition callback extension points are documented/named and guarded as explicit computation hooks.
- Tests assert saga plan compilation for known saga definitions.
