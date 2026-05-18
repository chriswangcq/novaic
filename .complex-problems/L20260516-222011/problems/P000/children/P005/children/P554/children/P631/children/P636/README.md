# RW Scratch Layout Cleanup and Test Update

## Problem

After inventory, remove root `/rw/scratch` as a default Workspace layout and update tests that encode the old global scratch convention, without breaking valid arbitrary `/rw` writes.

## Success Criteria

- Removes or updates high-confidence legacy root `/rw/scratch` initialization/contract references.
- Keeps generic `/rw` path behavior covered by tests using neutral or current subagent-aware paths.
- Preserves LogicalFS `RW_SCRATCH=/rw/subagents/{id}/scratch` behavior.
- Runs focused Cortex and LogicalFS tests.
