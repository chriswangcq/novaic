# P000: Shell CLI Residue Cleanup

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
The previous shell CLI tool surface audit proved the active LLM/Runtime path is clean, but it also found residue that can confuse future maintenance:

- `common.tools.definitions.BUILTIN_TOOLS` still exposes product metadata names `subagent_list` and `subagent_history`.
- `common.tools.definitions.HD_TOOLS` still carries direct `hd_*` metadata even though HD operations should be shell CLI capabilities via `devicectl hd ...`.
- `runtimectl` is installed as a shell command but only exposes help, making it a placeholder rather than a real capability.
- HD shell CLI coverage has implementation support for every proxy command but tests only round-trip `shell-exec`.

Clean these up physically instead of leaving compatibility residue. Do not preserve old direct tool metadata for backward compatibility.

## Success Criteria
- Active LLM schemas remain only `shell`, `display`, `skill_begin`, `skill_end`, and `sleep`.
- Runtime direct executors remain only `shell`, `display`, `skill_begin`, `skill_end`, and `sleep`.
- `BUILTIN_TOOLS` no longer contains `subagent_list` or `subagent_history`.
- HD direct metadata is no longer exported or mounted as active agent builtin tools.
- `runtimectl` is removed unless it has a real implemented subcommand surface.
- `devicectl hd` tests round-trip every HD proxy command: screenshot, mouse, keyboard, shell-exec, clipboard-get, clipboard-set, file-pull, and file-push.
- Prompt/schema/help text accurately advertises the shell CLI surface without vague ellipses.
- Targeted tests pass across Common, Business, Cortex, and Runtime.

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
