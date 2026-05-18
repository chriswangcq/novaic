# Direct session-ended delivery residue guard check

## Summary

Success. The one-go guard proved the direct P336 delivery boundary is free of the specific zero-generation compatibility residues named by this problem, and focused tests still pass.

## Evidence

- Source guard found no `session_generation or 0` fallback in `wake_finalize.py`.
- Source guard found no `if generation is None` presence-only validation in `session_handlers.py`.
- Source guard found no plain `generation: int` route schema in `routes.py`.
- `task_queue/client.py` contains `_require_positive_generation(generation)` before the `/api/queue/session-ended` request.
- Focused tests passed: `14 passed in 0.28s`.

## Criteria Map

- Direct boundary has no `session_generation or 0`: satisfied.
- Direct boundary has no handler `generation is None`-only validation: satisfied.
- Direct boundary has no plain non-positive route schema: satisfied.
- Any remaining direct residue removed: satisfied; no extra removal was needed after P341/P342.
- Focused finalize tests still pass: satisfied.

## Execution Map

- This was a guard-only check over the direct delivery files.
- No production code changed in P345.
- P345 depends on P341/P342 code changes and verifies their direct residue cleanup.

## Stress Test

- The guard specifically targets the old failure shape: "new validation exists, but old fallback remains active in the direct path." It found no direct-path fallback residue.

## Residual Risk

- Non-blocking for P345: test compatibility residue and upstream react defaults are intentionally handled by sibling P346/P347.

## Result IDs

- R325
