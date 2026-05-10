# P000: SubAgent tool schema cutover to shell

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
`subagent_spawn` is still exposed as a direct LLM-facing tool. The target shell-boundary design keeps only final harness tools outside shell; SubAgent coordination is an interface action and should be accessed through a shell capability command instead of a standalone tool schema.

## Success Criteria
- LLM-visible builtin schemas no longer include `subagent_spawn`.
- Shell schema advertises the replacement `agentctl subagent spawn` command.
- `agentctl subagent spawn` executes through the sandbox capability script and calls the existing Business spawn endpoint.
- Runtime schema/executor guard tests classify direct `subagent_spawn` as schema-cutover compatibility only.
- Targeted Runtime/Cortex/Common tests cover the new command path and schema cutover.

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
