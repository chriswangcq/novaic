# P364 Final Check: Recovery Compensation Finalize Aggregate Verification

## Verdict

`success`

## Criteria Map

- Focused recovery/compensation tests covering generation preservation and missing-identity rejection/reroute: satisfied by R345 and R346.
- Source/residue searches under `queue_service` for `wake_finalize`, `session_generation`, generation defaulting patterns: satisfied after the P365 follow-up removed the startup rebuild default.
- Map each P351 success criterion to concrete code/test evidence: satisfied.
- Record remaining gap as follow-up rather than marking P351 solved: satisfied; P365 was created, implemented, checked, and closed.

## Evidence

- R345: Compile and focused aggregate tests passed, but found the startup rebuild generation default.
- C366: P364 correctly refused success and opened P365.
- R346/C367: P365 removed the startup rebuild default and verified the fix.
- Aggregate suite after P365: `96 passed in 0.71s`.
- Residue search no longer finds production defaulting of missing `session_generation` to `1`.

## Stress Test

The aggregate check was deliberately skeptical:

- It checked direct compensation/recovery scope-end paths.
- It searched indirect session-state startup rebuild paths.
- It turned a discovered residue into a follow-up instead of accepting a partially clean result.
- It then re-closed P364 only after the follow-up had its own implementation and strict check.

## Residual Risk

No known P364-scoped residual risk remains. Broader session generation sentinel reads still exist in runtime-state conversions, but they are no-active/state-read sentinels rather than finalize mutation identity synthesis.
