# Upstream react generation default classification check

## Summary

Success for the classification problem. The result clearly identifies upstream react generation defaults as real architectural residue, but not a blocker for P336 delivery correctness because P341/P342 now fail closed before a malformed `session.ended` delivery can be accepted. The follow-on ownership is explicit: P337/P339 must remove the upstream defaults.

## Evidence

- R327 cites `react_think.py` default field and `from_context(...)` fallback to `0`.
- R327 cites `react_actions.py` default field and `from_context(...)` fallback to `0`.
- R327 cites both finalize-trigger builders forwarding `source.session_generation` into `wake_finalize`.
- R327 verifies direct P336 delivery guards are clean after P341/P342, so the upstream zero value cannot become an accepted `session.ended` delivery payload.

## Criteria Map

- Inspect `react_think.py`, `react_actions.py`, and tests: satisfied through source inspection and prior P346 test classification.
- Decide whether changing defaults is required for P336 parent success: satisfied; not required for P336 delivery correctness because bad values fail closed before accepted delivery.
- If not changed here, record exact follow-on ownership and guard P336: satisfied; ownership is P337/P339 and guard evidence is recorded.

## Execution Map

- Read-only classification; no code changed.
- Direct delivery guard evidence came from P341/P342/P345.
- This problem informs P343 parent and P336 aggregate verification.

## Stress Test

- Considered the failure mode where react defaults create `session_generation=0` and a malformed `session.ended` effect is accepted. P341 prevents payload construction and P342 prevents handler/route acceptance, so P336 delivery is fail-closed.
- Considered final-architecture risk: repeated wake-finalize failures if upstream contexts miss generation. That remains real and is deliberately not called solved here.

## Residual Risk

- Upstream react defaults remain a real cleanup item for P337/P339. This is non-blocking for P347 because the problem was classification, not implementation.

## Result IDs

- R327
