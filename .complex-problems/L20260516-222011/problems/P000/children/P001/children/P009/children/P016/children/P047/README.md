# Child Problem: ephemeral Cortex backing path residue

## Problem

Old outputs and docs may still mention `/tmp/novaic-cortex-sandbox-*` or encourage agents to reuse backing paths instead of `/cortex/ro`, `/cortex/rw`, `$RO`, or `$RW`.

## Success Criteria

- Active docs/prompts/tests do not instruct agents to reuse ephemeral backing paths.
- Any remaining ephemeral path references are historical failure examples or tests, clearly marked.
- Focused scan/classification exists.
