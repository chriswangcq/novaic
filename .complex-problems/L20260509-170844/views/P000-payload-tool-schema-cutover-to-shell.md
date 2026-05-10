# P000: Payload tool schema cutover to shell

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Direct payload tools (`payload_read`, `payload_search`, `payload_summarize`, `payload_qa`) are still exposed as LLM-facing tools even though the migration direction is to use filesystem/shell-oriented capabilities for interface tools. This keeps another old direct tool family active and prevents the final tool surface from shrinking toward `shell`, `display`, `skill_begin`, `skill_end`, and `sleep`.

## Success Criteria
- LLM-visible builtin schemas no longer include direct payload tools.
- Shell schema advertises the replacement payload capability command.
- A shell capability command can read/search Cortex payload files through stable `/cortex/ro` paths without exposing ephemeral sandbox paths.
- Runtime schema/executor guard tests treat payload direct executors as schema-cutover compatibility, not LLM-visible tools.
- Targeted Runtime/Cortex/Common tests cover the cutover and compatibility behavior.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R000: problems/P000/results/R000.md
- Check C000: problems/P000/checks/C000.md

## Follow-ups
- none
