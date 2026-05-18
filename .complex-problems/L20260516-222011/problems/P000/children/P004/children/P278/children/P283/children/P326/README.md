# Session generation lifecycle and advancement inventory

## Problem

Map where session generations are created, initialized, advanced, stored, and rebuilt across Queue Service session code. Verify the generation model has a single intended owner and no hidden increment/fallback path.

## Success Criteria

- File-reference every generation creation/advancement path in session repository, decision, ledger, rebuild, and tests.
- Explain the authoritative storage location for active generation.
- Identify whether generation changes are transactionally tied to the session state transition that needs them.
- Flag or fix any hidden generation generation/increment path outside the intended boundary.
