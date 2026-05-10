# Remove migrated direct executors from active Runtime

## Problem Definition

The active Runtime executor registry still exposes migrated interface tools directly even though the intended architecture is shell capability based. This keeps stale branches callable and makes tests prove compatibility instead of proving the new boundary.

## Proposed Solution

1. Remove migrated tool names from `_EXECUTORS`.
2. Remove now-unused imports/functions for direct IM, payload, subagent, audio, and device execution where they are not needed by final code.
3. Keep `shell`, `display`, `skill_begin`, `skill_end`, and `sleep` as the only Runtime tool executors.
4. Update tool-surface policy and tests so the invariant is final, not transitional.
5. Update or remove direct-executor unit tests that only validate old compatibility behavior.
6. Run focused tests that cover final tool schema, shell capabilities, unknown tool handling, and lifecycle behavior.

## Acceptance Criteria

- `sorted(_EXECUTORS)` equals `['display', 'shell', 'skill_begin', 'skill_end', 'sleep']`.
- Direct execution of a migrated tool name returns the normal unknown-tool failure path.
- No Runtime test imports removed direct executor functions.
- The shell capability tests still prove the migrated behaviors exist via shell commands.
- Tool-surface tests no longer expect non-final direct tools.

## Verification Plan

- Run a Python executor inventory check.
- Run focused Runtime tests for tool handler behavior, prompt/finalizer behavior, and tool surface contracts.
- Run Cortex shell capability tests to verify shell replacements still work.
- Run Common schema/contract tests to verify LLM surface remains five tools.

## Risks

- Some tests may still model old direct tool calls as historical examples; these should be updated only if they are asserting active execution, not if they are testing historical observation rendering.
- Physical deletion may reveal imports that were accidentally serving as undocumented dependencies.

## Assumptions

- The migration target is final harness plus shell capabilities, not backward-compatible direct execution.
- The current system does not need to complete stale queued `tool.execute` messages for removed direct tool names.
