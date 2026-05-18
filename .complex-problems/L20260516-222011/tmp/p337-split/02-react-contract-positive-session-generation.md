# React contract positive session generation

## Problem

`ReactThinkInput` and `ReactActionsInput` still default missing `session_generation` to `0`, and finalize-trigger builders forward that value into wake-finalize context. Runtime finalize enforcement should require explicit positive session generation at these upstream contract boundaries.

## Success Criteria

- Remove `session_generation: int = 0` and `ctx.get("session_generation") or 0` defaults from react contracts where they feed finalize.
- Missing or non-positive session generation fails before finalize-trigger payload creation.
- Update tests that currently assert default `session_generation=0`.
- Verify valid positive generation still flows into prepare/LLM/finalize payloads.
