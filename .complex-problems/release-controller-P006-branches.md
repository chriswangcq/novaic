# Inspect and clean stale local branches

## Problem

The local repository has several old branches. Clean stale local branches only after inspecting whether they are merged or contain unique work that should not be deleted.

## Success Criteria

- Current branch remains `main`.
- Local branches are listed and inspected.
- Branches deleted locally are safe stale branches or already merged branches.
- Branches with unique unmerged work are preserved and documented.
- No uncommitted work is reverted.
