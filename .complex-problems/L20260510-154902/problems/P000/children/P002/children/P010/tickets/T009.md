# Verify ContextEvent substrate boundaries and non-integration

## Problem Definition

Phase 1 introduced ContextEvent schema/store code. P010 must verify that the substrate is deterministic, covered by tests, and not silently half-integrated into current Cortex write/read paths.

## Proposed Solution

- Run focused ContextEvent tests.
- Run relevant existing Cortex context/workspace tests to catch regressions.
- Inspect code/diff for:
  - hidden `uuid`, wall-clock, env, or file-source dependencies in event substrate;
  - accidental endpoint cutover;
  - new permanent dual-source behavior;
  - stale old-source claims in touched files.
- Record exact verification commands and residual gaps for later phases.

## Acceptance Criteria

- Focused ContextEvent tests pass.
- Relevant existing Cortex tests pass.
- Static search confirms no hidden time/id/env dependency in the substrate domain logic.
- Diff review confirms no current write/read endpoint has been silently cut over or double-wired.
- Known remaining integration work is explicitly recorded for P003-P006.

## Verification Plan

- Run focused event tests.
- Run selected existing workspace/context tests.
- Run `git diff -- novaic-cortex/novaic_cortex novaic-cortex/tests` and inspect touched files.
- Run static searches for legacy terms and hidden dependency terms.

## Risks

- Running only focused tests may miss a subtle package import regression; include at least relevant existing tests.
- Diff may include pre-existing `novaic-cortex` changes from prior work; distinguish new substrate changes from existing changes.

## Assumptions

- Full endpoint cutover is not part of Phase 1.
