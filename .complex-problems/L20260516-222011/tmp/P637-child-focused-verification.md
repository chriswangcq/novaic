# Final RW Scratch Focused Verification

## Problem

After residue classification, the focused tests that protect Cortex layout, neutral RW paths, subagent scratch behavior, and LogicalFS generic path behavior need to pass in the current worktree.

## Success Criteria

- Runs focused Cortex workspace/path/runtime/sandboxd tests affected by the cleanup.
- Runs LogicalFS layout/authority tests with explicit dependency paths.
- Records commands and outputs, including any corrected rerun if dependency setup is wrong.
- Converts any failing focused test into a follow-up instead of ignoring it.
