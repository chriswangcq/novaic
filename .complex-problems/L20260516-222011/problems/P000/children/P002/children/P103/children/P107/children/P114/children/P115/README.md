# Stable Workspace Path Guidance in Shell Schema and Help

## Problem

The LLM-facing shell schema and generated Cortex shell help must consistently teach agents to use stable `/cortex/ro`, `/cortex/rw`, `$RO`, and `$RW` paths, and not copied `novaic-cortex-sandbox-*` backing paths.

## Success Criteria

- Inspect canonical shell schema for stable path guidance.
- Inspect generated `cortex --help` and related help text for stable path guidance.
- Fix any missing guidance and add or run focused schema/help guards.
- Confirm no public help text encourages copied `novaic-cortex-sandbox-*` paths.
