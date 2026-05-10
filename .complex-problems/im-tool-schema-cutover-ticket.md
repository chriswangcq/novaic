# Remove IM tools from LLM-visible schema

## Problem Definition

The old direct IM tools remain visible to the LLM even though `agentctl im` now provides shell equivalents. This creates two active ways to do the same thing and increases the chance that new code exists while the old branch still runs.

## Proposed Solution

Cut the LLM-facing schema over for IM tools:

- Remove environment IM schemas from `AGENT_BUILTIN_TOOL_SCHEMAS`.
- Update no-tool warning and shell description to direct agents to `agentctl im reply/read`.
- Update turn-finalizer pure logic to recognize `shell` commands that invoke `agentctl im reply`.
- Update guard tests so direct IM executors can exist only as internal compatibility, not as visible schemas.

## Acceptance Criteria

- Static tool schemas exclude all direct IM tool names.
- Final visible schemas still include `shell`, `display`, `skill_begin`, `skill_end`, and `sleep`.
- `is_reply_no_followup()` returns true for a single `shell` tool call whose command invokes `agentctl im reply`.
- Existing direct environment handler tests still pass, proving compatibility behavior is not accidentally broken.

## Verification Plan

- Run schema guard tests.
- Run turn finalizer tests.
- Run environment handler tests.
- Run Runtime/Cortex shell capability tests.

## Risks

- Prompt text may still mention old direct tools in Business defaults. If tests expose active prompt residue, fix it in this ticket.
- Direct executor deletion should wait until payload/subagent/audio/device cutovers are also ready or have their own deletion gates.

## Assumptions

- The current cutover scope is IM only; payload/subagent/audio/device remain visible until their shell equivalents are implemented.
