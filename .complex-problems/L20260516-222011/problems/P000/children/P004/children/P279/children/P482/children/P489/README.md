# Finalize ownership cleanup

## Problem

Finalize behavior must be owned by explicit event/FSM decisions with reason, generation, and remaining stack semantics. Any stale finalize compatibility branch that clears active state directly, tolerates missing generation, or hides dangling child skills creates the same class of bug the session FSM work was meant to eliminate. This belongs under P482 because finalize is the highest-risk compatibility surface.

## Success Criteria

- Finalize production code is inspected against the P482 inventory.
- High-confidence stale finalize branches are removed or tightened.
- Any retained compatibility-looking finalize branch has a documented reason and a focused guard test.
- Focused finalize ownership/session-end tests pass.
