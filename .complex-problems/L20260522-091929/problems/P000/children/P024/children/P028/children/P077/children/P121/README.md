# Commit Push And Deploy Queue Postgres Cutover Code

## Problem

Production cutover must not depend on a dirty local workspace or an ad hoc patched staging checkout. The Queue Postgres fixes discovered during staging need to be committed, pushed, and made available to the production runtime before any production migration or restart.

## Success Criteria

- Queue-related source changes are reviewed, tested, committed, and pushed in the relevant submodule/repo.
- Root repository pointers or ledger artifacts required for reproducibility are committed or explicitly separated from runtime deploy commits.
- The api production/staging runtime checkout can fetch the pushed commit.
- The deployed runtime source matches the committed code that passed tests.
- Unrelated dirty workspace changes are left untouched and explicitly not mixed into the cutover commit.
