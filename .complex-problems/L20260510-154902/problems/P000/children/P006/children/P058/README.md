# Legacy DFS deletion inventory

## Problem

Identify whether the legacy DFS `ContextEngine` / `StepTree` modules and tests can be physically deleted now, or which specific debug/projection verification cases still need migration to event projection tests first.

## Success Criteria

- All `ContextEngine`, `StepTree`, and DFS test usages are listed and classified.
- Active production/API/runtime dependencies are distinguished from tests/debug references.
- A deletion or migration plan is recorded with exact files.
