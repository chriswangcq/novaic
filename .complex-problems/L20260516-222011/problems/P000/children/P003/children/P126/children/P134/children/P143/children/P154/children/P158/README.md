# LLM prepare authority residue guard

## Problem

The prepare path needs a guard test so future code cannot reintroduce `context.jsonl`/`read_context` authority without review.

This belongs under `P154` because static/source evidence can regress unless captured in tests.

## Success Criteria

- Existing guard coverage is identified or a new guard is added.
- Guard fails if LLM prepare assembly starts using `read_context`/`context/read` as authority.
- Focused tests pass.
