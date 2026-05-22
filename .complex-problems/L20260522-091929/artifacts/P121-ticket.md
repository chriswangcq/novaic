# Commit Push And Deploy Queue Postgres Cutover Code

## Problem Definition

The staging validation fixes currently live in the local `novaic-agent-runtime` working tree and the api staging checkout. Production cutover must not rely on uncommitted patches, and unrelated dirty root workspace changes must not be mixed into the cutover commit.

## Proposed Solution

Review the runtime diff, run the focused regression tests, commit only the Queue Postgres runtime fixes in `novaic-agent-runtime`, push the submodule branch, then update the api runtime checkout to the pushed commit. In the root repo, record or separate ledger/submodule pointer state without staging unrelated dirty files.

## Acceptance Criteria

- `novaic-agent-runtime` Queue Postgres source changes are committed and pushed to the active branch.
- Focused tests pass before commit.
- The api runtime checkout can fetch and is updated to the pushed commit.
- Root repository unrelated dirty changes are not staged or reverted.
- Any remaining root-level ledger/submodule pointer state is reported explicitly.

## Verification Plan

Use `git diff` and `git status --short` before staging, stage only intended runtime files, run the focused pytest set, commit and push, verify remote branch contains the commit, then update api runtime checkout and confirm its `HEAD` matches the pushed commit.

## Risks

- Accidentally staging unrelated user changes in the root workspace.
- Pushing runtime code before all staging-discovered regression tests pass.
- The api checkout may have local patches; update must preserve or replace only the patches now represented by the pushed commit.

## Assumptions

- The active runtime branch is the correct branch to continue from unless git status shows otherwise.
- Ledger artifacts may remain root-local until a separate root commit is intentionally made.
