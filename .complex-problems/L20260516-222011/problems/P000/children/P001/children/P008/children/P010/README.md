# Git and submodule state fact capture

## Problem

Capture the current git branch, dirty state, and submodule pointer state for the superproject and key submodules. This is read-only evidence needed before optimization.

## Success Criteria

- Superproject branch and dirty state are recorded.
- Submodule status is summarized.
- Key submodule dirty states are sampled or checked.
- Result explicitly states whether implementation files were modified during this fact capture.
