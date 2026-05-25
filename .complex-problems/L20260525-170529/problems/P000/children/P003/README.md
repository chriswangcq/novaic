# Verify, clean, and commit structured activity title change

## Problem

The cross-repo change must be proven and committed cleanly. The current working tree already contains a frontend hotfix; the final state must include runtime/frontend/contract tests, a focused diff review, and commits in affected subrepos plus the parent repo gitlink update.

## Success Criteria

- Focused runtime tests pass.
- Focused frontend ActivityTimeline tests pass.
- Relevant lint/type checks are run; unrelated pre-existing failures are documented.
- Git status is reviewed to avoid unrelated changes.
- Affected subrepos are committed with clear messages.
- Parent repo is committed with updated submodule pointers and ledger artifacts.
