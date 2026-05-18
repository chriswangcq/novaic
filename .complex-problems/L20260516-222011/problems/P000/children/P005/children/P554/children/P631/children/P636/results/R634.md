# RW Scratch Layout Cleanup and Test Update Result

## Summary

Completed the root `/rw/scratch` cleanup for Cortex. `Workspace.initialize()` no longer creates global root scratch, Cortex tests no longer use root `/rw/scratch` as a generic/canonical fixture, and the current subagent-aware scratch contract remains intact through `RW_SCRATCH=/cortex/rw/subagents/{id}/scratch`.

## Completed Children

- P638 removed the default `/rw/scratch` layout entry from `novaic-cortex/novaic_cortex/workspace.py` and updated the direct Workspace initialization assertion.
- P639 rewrote Cortex test fixtures from root `/rw/scratch` to neutral `/rw/tmp` while preserving workspace, runtime, metric, chaos, hook, and path-abuse invariants.
- P640 ran final residue scans and verified remaining root `/rw/scratch` hits are either a negative Cortex guard or lower-layer LogicalFS generic tests.

## Changes

- `novaic-cortex/novaic_cortex/workspace.py`: removed root `/rw/scratch` from default `initialize_layout`.
- `novaic-cortex/tests/test_workspace.py`: asserts old `rw/scratch/.keep` is absent and uses `/rw/tmp` for generic writable fixture paths.
- `novaic-cortex/tests/test_workspace_limits.py`, `test_workspace_authority.py`, `test_runtime.py`, `test_cortex_chaos.py`, `test_hooks_limits.py`, `test_tool_metrics.py`, `test_wave4_metrics.py`, `test_paths_adversarial.py`, `test_runtime_path_abuse.py`, and `test_workspace_paths.py`: generic root scratch fixtures rewritten to `/rw/tmp`.

## Verification

- P638 focused Workspace initialization tests: 2 passed.
- P641 workspace/authority focused tests: 22 passed.
- P642 runtime/tool focused tests: 14 passed.
- P643 path-abuse focused tests: 47 passed.
- P640 aggregate Cortex suite: 88 passed.
- P640 corrected LogicalFS focused rerun: 9 passed.
- P640 post-scan confirmed Cortex no longer advertises root `/rw/scratch` as default/canonical scratch.

## Known Gaps

- Lower-layer LogicalFS tests still use `/rw/scratch` as an arbitrary generic path. That is intentionally classified out of Cortex semantic scope and does not reintroduce the old Cortex default layout.
