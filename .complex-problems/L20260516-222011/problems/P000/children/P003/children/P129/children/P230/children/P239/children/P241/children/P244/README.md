# Verify mixed runtime and Cortex pytest selection is stable

## Problem

After namespace cleanup, the previously failing mixed focused pytest command must pass in one process. This belongs under the namespace cleanup ticket because the goal is not just local Cortex tests, but cross-package verification stability.

## Success Criteria

- The combined focused command for `novaic-agent-runtime/tests/test_tool_surface_boundary.py` and `novaic-cortex/tests/test_tool_schemas_limits.py` passes in one pytest process.
- A scan confirms Cortex tests no longer contain generic `tests.*` imports.
- Any remaining top-level `tests` package ambiguity is documented as unrelated or removed when it affects the mixed command.
