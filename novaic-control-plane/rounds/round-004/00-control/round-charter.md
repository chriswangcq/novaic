# Round 004 Charter

## Window
- Round ID: round-004
- Round status: ACTIVE
- Cadence: sync and submission happen within the round

## Objective
Complete the first real split wave by moving production code and runtime wiring to split repos.

## Scope
- Move gateway/runtime/tools/storage and agent-runtime code into split repos
- Remove or replace monorepo direct imports with split-repo-compatible wiring
- Prove startup/health in split repos from repo root
- Prove one cross-repo call path and one desktop external mode path

## Success Criteria
- At least 3 split repos land new migration commits this round
- At least 2 split repos pass startup/health from split repo roots
- Monorepo paths touched by migration are reduced, shimmed, or redirected
- Every DONE item includes commit SHA, migrated paths, and runnable evidence
