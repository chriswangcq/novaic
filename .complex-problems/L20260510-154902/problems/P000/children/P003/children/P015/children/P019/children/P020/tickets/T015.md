# Implement closed-scope fold rendering

## Problem Definition

The projector tracks skill scope stack, but closed scopes do not yet render folded summaries or expose structural child folds. P020 must add scope-local message buffers and render close behavior without introducing Workspace/DFS reads.

## Proposed Solution

- Refactor projection internals to keep pure in-memory scope state.
- Route `ContextMessageAppended` into the referenced open skill scope when `payload.scope_id` matches an open scope; otherwise keep root-level behavior.
- On `SkillScopeClosed`:
  - validate LIFO as before;
  - if `report` is non-empty, append `[Skill '<name>' completed]\n<report>` to parent message stream;
  - if `report` is blank, append buffered child fold messages to parent message stream without empty summary.
- Add tests for non-empty fold, blank close, and nested structural fold.

## Acceptance Criteria

- Closed non-empty scopes produce folded summary messages.
- Blank closed scopes do not emit empty summaries.
- Nested structural close exposes child fold output.
- Existing projection tests still pass.

## Verification Plan

- Run focused projection/substrate tests.
- Static scan projector for hidden dependencies.

## Risks

- Refactor may break P014/P018 behavior; run all projection tests.

## Assumptions

- Stale sibling suppression remains separate in P021.
