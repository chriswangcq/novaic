# Submodule git state capture

## Problem

Capture submodule pointers and dirty states for active submodules so later changes are attributed to the correct repository.

## Success Criteria

- `git submodule status` is summarized.
- Key changed or active submodules have `git status --short` checked.
- Dirty submodule markers are explained if present.
- No code edits are made.
