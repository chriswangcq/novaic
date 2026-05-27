# Commit and push touched subrepos

## Problem

Submodule repositories must be committed and pushed before the root repository can point at their deployable SHAs.

## Success Criteria

- `novaic-llm-factory` commit exists on `origin/main`.
- `novaic-agent-runtime` commit exists on `origin/main`.
- `novaic-app` commit exists on its remote branch if source changes are retained.
- Commit SHAs and push results are recorded.
