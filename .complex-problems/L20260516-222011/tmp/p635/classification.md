# RW Scratch Usage Classification

## Scan Commands

Recorded in `.complex-problems/L20260516-222011/tmp/p635/scratch-scan.txt`:

- `rg -n "/rw/scratch|RW_SCRATCH|/rw/subagents|initialize_layout|scratch" novaic-cortex novaic-logicalfs || true`
- `rg -n "writable_env|RW_PUBLIC|RW_SELF|RW_TMP|RW_ARTIFACTS|RW_SCRATCH" novaic-cortex novaic-logicalfs || true`

## Current Intended Contract

- `novaic-cortex/novaic_cortex/logical_fs.py:259-277`
  - Classification: intended current shell RW layout.
  - `RW_SCRATCH` points at `/cortex/rw/subagents/{subagent_id}/scratch`.
- `novaic-cortex/novaic_cortex/logical_fs.py:191-215`
  - Classification: intended bounded RW working-set materialization.
  - Root files, `/rw/public`, `/rw/system`, and current `/rw/subagents/{id}` are mounted; broad old root scratch tree is not specially mounted.
- `novaic-cortex/tests/test_sandboxd_wiring.py:134-156`
  - Classification: current intended test for subagent-scoped RW materialization.

## Removable Legacy Cortex Layout

- `novaic-cortex/novaic_cortex/workspace.py:976-986`
  - Classification: removable default global scratch layout.
  - `Workspace.initialize()` still creates `/rw/scratch/.keep` by default.
- `novaic-cortex/tests/test_workspace.py:15-20`
  - Classification: stale initialization expectation; should stop expecting `rw/scratch` default layout.

## Cortex Generic RW Fixture Hits To Rewrite

These hits use `/rw/scratch` mostly as a convenient arbitrary writable path, not as a behavior that must stay global. P636 should rewrite them to neutral `/rw/tmp/...`, `/rw/public/...`, or subagent-aware `/rw/subagents/main/scratch/...` depending on the test's purpose:

- `novaic-cortex/tests/test_workspace.py:32`
- `novaic-cortex/tests/test_workspace_limits.py:17,62,71-74`
- `novaic-cortex/tests/test_workspace_authority.py:16`
- `novaic-cortex/tests/test_runtime.py:43,49`
- `novaic-cortex/tests/test_runtime_path_abuse.py:32-33,56`
- `novaic-cortex/tests/test_paths_adversarial.py:33,48,64,91,130-131,148`
- `novaic-cortex/tests/test_cortex_chaos.py:76-79`
- `novaic-cortex/tests/test_hooks_limits.py:115`
- `novaic-cortex/tests/test_tool_metrics.py:29`
- `novaic-cortex/tests/test_wave4_metrics.py:29-30`

## Lower-Layer LogicalFS Generic Tests

- `novaic-logicalfs/tests/test_authority.py:68-87,109-119`
  - Classification: lower-layer arbitrary logical path authority tests. They prove object-key mapping/read-write/delete/initialize_layout on arbitrary paths, not Cortex's default workspace layout.
  - P636 may leave these unchanged unless the final architecture wants to ban the string globally.
- `novaic-logicalfs/tests/test_logicalfs.py:15-43`
  - Classification: local provider generic cwd/env layout test. The `cwd="scratch"` stable path is a generic provider fixture, not Cortex's `RW_SCRATCH` contract; Cortex passes no default `cwd` for shell unless caller supplies one.

## P636 Edit Targets

- Remove `"/rw/scratch"` from `Workspace.initialize()` default layout.
- Update `test_initialize_creates_layout` to assert current root layout and/or current subagent-aware scratch behavior elsewhere.
- Rewrite Cortex tests that use `/rw/scratch` as generic fixture paths.
- Keep `logical_fs.py` `RW_SCRATCH` and `test_sandboxd_wiring.py` subagent-scoped scratch assertions.
