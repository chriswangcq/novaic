# Superproject git state capture

## Problem

Capture the superproject branch, status, recent commit, and current ledger side effects so later code edits are interpreted correctly.

## Success Criteria

- Branch name and top commit are recorded.
- `git status --short` is recorded and interpreted.
- New ledger files are distinguished from implementation edits.
- No code edits are made.
