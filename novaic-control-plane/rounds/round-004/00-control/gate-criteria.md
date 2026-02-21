# Round 004 Gate Criteria

## Gate A - Code Migration
- DONE requires `commit_sha` and `migrated_paths` with source -> target mapping.
- Doc-only output without code changes is not accepted.

## Gate B - Split Repo Operability
- At least 2 split repos pass startup/health from their own repo roots.
- Commands and PASS markers must be replayable by non-authors.

## Gate C - Runtime Wiring
- Monorepo call sites touched in this round must point to split-compatible endpoints/imports.
- At least one cross-repo call path is replayed and marked PASS.

## Gate D - Execution Discipline
- Teams provide runnable output, not analysis-only updates.
- Incomplete items include blocker owner and `target_round`.

## Fail Conditions
- DONE without commit SHA
- DONE without migrated path mapping
- script output claimed PASS but no corresponding code migration
