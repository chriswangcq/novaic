# Finalize saga and session handler residue classification

## Problem

`wake_finalize.py`, `subagent_wake.py`, and `session_handlers.py` carry finalize/session-ended identity to the Queue session boundary. They must fail closed for missing/stale session generation and preserve finalize reason/remaining stack explicitly.

## Success Criteria

- Inspect finalize saga and session handler guard hits.
- Confirm session generation is validated with explicit positive-generation contracts.
- Confirm finalize reason and remaining stack are required before session-ended mutation.
- Patch and test any dangerous fallback.
- Run focused finalize/session handler tests.
