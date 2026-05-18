# Hidden input remediation tests and guards success check

## Summary

P474 is now successful after follow-up P478. The initial run exposed a cwd mistake, and the follow-up rerun from the correct cwd passed the focused suite and guards.

## Evidence

- R462 recorded the first failed run and clean guard output.
- R463 reran the focused suite from `novaic-agent-runtime` and passed: `47 passed in 0.19s`.
- R463 guard output remains clean for runtime env reads, decision-adapter `ServiceConfig` reads, and old monkeypatch patterns.

## Criteria Map

- Focused pytest suite passes: satisfied by R463.
- No direct decision-path `ServiceConfig.MAX_*` reads remain: satisfied by R463 guard.
- No runtime queue/task raw environment reads remain: satisfied by R463 guard.
- Old focused-test monkeypatch patterns are gone: satisfied by R463 guard.

## Execution Map

- T468 one-go produced R462, which failed due cwd.
- P478 follow-up reran verification correctly and produced R463.
- This check cites both results so the failed first attempt remains visible.

## Stress Test

- Plausible failure mode: a failed first run gets ignored. This check explicitly includes R462 and explains why R463 closes the gap.
- Plausible failure mode: guard passes but tests fail. R463 includes both passing tests and guard artifacts.

## Residual Risk

- Non-blocking: broader parent checks still need aggregate verification after P470/P471.

## Result IDs

- R462
- R463
