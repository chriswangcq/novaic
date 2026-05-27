# Run final pre-push focused verification

## Problem

Before committing deployable source, touched code should have fresh focused verification evidence so the pushed commit is not stale relative to local tests.

## Success Criteria

- Focused tests pass for `novaic-llm-factory` streaming route/provider behavior.
- Focused tests pass for `novaic-agent-runtime` stream parsing, handler, and projection behavior.
- Focused tests pass for `novaic-app` timeline/contract guard behavior or App is explicitly marked non-server-release-only.
- Git status for touched repos is captured before commit.
