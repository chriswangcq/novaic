# Audit shell capability and tool CLI migration

## Problem

Find any remaining tool/harness surfaces that should now be shell CLI based but are still exposed or wired through old direct tools, missing agent identity binding, missing subagent binding, missing internal auth, or non-CLI paths.

## Success Criteria

- Inspect tool schema generation, shell capability scripts, runtime tool handlers, and monitor/desc wiring.
- Verify shell execution has explicit capability env and generated CLIs.
- Identify direct legacy harness tools that remain live without clear reason.
- Record evidence and any follow-up fixes.
