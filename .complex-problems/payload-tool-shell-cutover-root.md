# Payload tool schema cutover to shell

## Problem

Direct payload tools (`payload_read`, `payload_search`, `payload_summarize`, `payload_qa`) are still exposed as LLM-facing tools even though the migration direction is to use filesystem/shell-oriented capabilities for interface tools. This keeps another old direct tool family active and prevents the final tool surface from shrinking toward `shell`, `display`, `skill_begin`, `skill_end`, and `sleep`.

## Success Criteria

- LLM-visible builtin schemas no longer include direct payload tools.
- Shell schema advertises the replacement payload capability command.
- A shell capability command can read/search Cortex payload files through stable `/cortex/ro` paths without exposing ephemeral sandbox paths.
- Runtime schema/executor guard tests treat payload direct executors as schema-cutover compatibility, not LLM-visible tools.
- Targeted Runtime/Cortex/Common tests cover the cutover and compatibility behavior.
