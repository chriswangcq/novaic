# P365 Check: Remove Startup Rebuild Generation Default

## Verdict

`success`

## Criteria Map

- No production code under session rebuild defaults missing `session_generation` to `1`: satisfied.
- Startup rebuild records active session only when saga context carries positive explicit generation: satisfied by DB-backed tests.
- Missing/invalid generation contexts are skipped without fabricating active session state: satisfied by missing, `None`, `0`, `"0"`, `"bad"`, `False`, and `-1` tests.
- Existing session rebuild boundary/residue tests still pass: satisfied.

## Evidence

- `queue_service/session_rebuild.py` now parses generation with `_positive_session_generation`.
- `record_active_session` is reached only after `session_generation is not None`.
- Focused tests passed: `23 passed in 0.23s`.
- Aggregate recovery/finalize/rebuild suite passed: `96 passed in 0.71s`.
- Residue search found no production `session_generation` fallback to `1`.

## Stress Test

The check included both valid and invalid serialized forms:

- Positive integer generation.
- Positive numeric-string generation.
- Missing generation.
- Explicit `None`, zero, zero string, non-numeric string, boolean, and negative generation.

It also caught and updated stale tests still naming the old attach publish method, so the guard suite now reflects the current outbox-recording semantics rather than preserving misleading legacy wording.

## Residual Risk

No scoped residual risk remains. Historical malformed running saga rows will now be skipped during startup rebuild, which matches the no-backward-compatibility direction.
