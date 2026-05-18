# Attach generation compatibility cleanup

## Problem

Attach handling must reject stale or missing generation inputs through explicit FSM/session state semantics, not legacy fallback behavior. Any no-generation attach compatibility path can make a new message attach to the wrong wake or hide session corruption. This belongs under P482 because attach/generation residue is a direct source of old wake-loop failures.

## Success Criteria

- Attach/generation production paths are inspected against the P482 inventory.
- Missing-generation and stale-generation handling is explicit and deterministic.
- High-confidence legacy no-generation compatibility paths are removed or converted to strict guard behavior.
- Focused attach/generation tests pass.
