# Check: Session Locking Needs Behavioral Race Coverage

## Summary

`R085` implements the correct Postgres locking primitives and wires them into the session decision paths, and the focused SQL/source-order verification is useful. The original problem is not fully solved yet because the success criteria explicitly call for first-dispatch race, attach/finalize revalidation, and no-input-loss coverage in the Postgres path. The current tests prove SQL shape and call ordering, but they do not execute a behavioral race/revalidation scenario through the repository.

## Blocking Gaps

- No behavioral Postgres-path test exercises first dispatch when the state row is missing and verifies the locked decision still records durable input before start/restart transition.
- Attach revalidation is guarded by source-order tests, but there is no runtime test that simulates the active session changing between the initial dispatch read and the after-transaction attach write.
- Finalize/no-input-loss is covered by existing SQLite-session regressions plus source-order checks, but not by a Postgres-mode behavioral test that asserts pending inputs remain restartable under the locked finalize path.
- `R085` explicitly records the absence of live or behavioral Postgres race coverage as a known gap.

## Result IDs

- R085
