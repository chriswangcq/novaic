# P364 Check: Recovery Compensation Finalize Aggregate Verification

## Verdict

`not_success`

## Criteria Map

- Focused recovery/compensation tests covering generation preservation and missing-identity rejection/reroute: mostly satisfied.
- Source/residue searches under `queue_service` for `wake_finalize`, `session_generation`, generation defaulting patterns: executed and found one relevant residue.
- Map each P351 success criterion to concrete code/test evidence: partially satisfied; one startup rebuild path violates the identity principle.
- Record remaining gap as follow-up rather than marking P351 solved: satisfied by this check.

## Evidence

- Compile succeeded for recovery/finalize modules and focused tests.
- Focused aggregate pytest run passed: `73 passed in 0.53s`.
- Compensation path now rejects missing/invalid generation before creating `wake_finalize`.
- Recovery archive path now requires positive generation before publishing `CORTEX_SCOPE_END`.
- Residue search found `queue_service/session_rebuild.py:35` uses `generation=int(context.get("session_generation") or 1)`.

## Stress Test

The skeptical check searched not only direct `CORTEX_SCOPE_END` publishers but also startup/session-state rebuild paths, because a stale or missing identity can later affect attach/finalize behavior even if it is not itself a scope-end publisher.

## Residual Risk

`session_rebuild.py` can currently convert a missing `session_generation` in a running saga context into a valid active session generation `1`. That is a compatibility fallback and should be removed before P351 can be considered clean.

## Required Follow-Up

Create a child problem to remove the startup rebuild generation default, require explicit positive `session_generation`, and test that missing/invalid contexts are skipped.
