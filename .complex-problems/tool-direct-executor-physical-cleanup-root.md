# Tool direct executor physical cleanup

## Problem

The shell boundary cutover removed IM, payload, subagent, audio, and device tools from the LLM-facing schema, but Runtime still keeps their old direct executors in `_EXECUTORS`. This creates misleading residue: new code paths work, yet old paths can still be called internally and tested as active behavior. The user's principle is no compatibility residue after migration unless explicitly justified.

This problem covers physically removing migrated interface-tool direct execution paths from the active Runtime executor registry, updating tests to assert the final harness shape, and keeping only genuinely needed non-LLM command/schema contracts.

## Success Criteria

- Runtime `_EXECUTORS` contains only final harness tools: `shell`, `display`, `skill_begin`, `skill_end`, `sleep`.
- IM, payload, subagent, audio, and device tools are not accepted as direct Runtime tool executions.
- LLM-facing schemas remain exactly the five final harness tools.
- Tests assert migrated tool names are shell capabilities only, not active executors.
- Legacy helper code that becomes unreachable after registry cleanup is physically removed where safe; any retained contract modules are explicitly documented as non-LLM/non-runtime command-contract references.
- Focused Runtime, Cortex, and Common tests pass.
