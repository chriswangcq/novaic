# Recommended RO/RW Mount Optimization Design

## Summary

Recommended target: keep the user-facing `/cortex/ro` and `/cortex/rw` shell contract, but replace "always rebuild full temporary trees from BlobStore" with a staged `MountPlan` substrate:

```text
ShellCommand + cwd + explicit mount profile
  -> MountPlanner
  -> MountManifestSnapshot
  -> LocalObjectCache
  -> TempExecTree
  -> WriteJournal
  -> CortexStore commit
```

The design should be implemented in phases so correctness stays ahead of speed. FUSE/OverlayFS are useful mental models but should not be the first substrate.

## Done

### Target Architecture

1. `MountPlanner`
   - Inputs: command, cwd, timeout, explicit shell args, capability env, current agent/subagent/scope.
   - Output: a `MountPlan` with `ro_mode`, `rw_mode`, `paths`, and `reason`.
   - Modes:
     - `control`: no historical RO/RW hydration; create empty temp RW with capability env only.
     - `rw_empty`: empty writable RW, persist created/modified files.
     - `rw_full`: hydrate full RW before exec, persist delta after exec.
     - `ro_none`: no RO hydration.
     - `ro_scope`: hydrate current subagent/root/wake scope plus config/tool metadata.
     - `ro_full`: hydrate full agent RO.
   - Default starts conservative; faster modes are enabled only when tests and metrics prove safe.

2. `MountManifestSnapshot`
   - Store manifest entries for `/ro` and `/rw`: logical path, size, hash or etag, content type, modified generation, zone.
   - Avoid recursive listing and per-object metadata discovery on every exec.
   - Enables cheap "what changed?" planning and cache validation.

3. `LocalObjectCache`
   - Per tenant/agent cache under the Cortex service runtime directory.
   - Keyed by content hash/etag, not by mutable logical path.
   - RO files can be linked from cache into temp exec trees.
   - RW files should be copied or reflinked into temp exec trees; do not hardlink mutable RW files into shared cache.
   - Cache entries are validated by manifest generation before use.

4. `TempExecTree`
   - Still creates a temp process tree per shell command, preserving disposable process semantics.
   - Populates the tree from cache/manifest according to `MountPlan` instead of blindly downloading all objects.
   - Keeps stable env and path rewrite behavior.

5. `WriteJournal`
   - Replaces full before/after recursive RW stat scans over time.
   - Phase 1 can keep stat scanning for compatibility.
   - Later phases record known writes/deletes from the temp tree and commit changed files only.
   - Commit is still through CortexStore, preserving durability and audit.

### Phased Plan

Phase 0: Measurement and Guardrails

- Add per-command metrics:
  - `mount_plan`
  - `include_ro/include_rw`
  - object count listed
  - bytes downloaded
  - materialize duration
  - process duration
  - RW scan duration
  - bytes uploaded
  - cache hit/miss once cache exists
- Add structured logs around `_materialize_workspace`, `_persist_rw_changes`, and `/v1/internal/shell`.
- No behavior change.

Phase 1: Explicit Mount Profiles

- Extend shell request/tool contract with optional mount hints, for example:
  - `mount_profile=auto|control|rw_empty|rw_full|ro_scope|ro_full`
  - or explicit `ro_mode` / `rw_mode`.
- Keep current behavior as default initially.
- Route clear CLI-only commands (`agentctl im read`, `agentctl im reply`, `cortex payload read`, `devicectl hd screenshot`) through `control` unless they reference `/cortex/rw` files.
- Add monitor display of chosen mount profile in shell step diagnostics.

Phase 2: Manifest Snapshot

- Maintain `/ro/.cortex_manifest.json` and `/rw/.cortex_manifest.json` or an internal manifest table/object.
- Update manifest on `Workspace` writes, deletes, scope creates, step writes, payload writes, and archive moves.
- Sandbox uses manifest for planning, sync estimates, and path selection instead of recursive list as the first operation.
- Keep fallback recursive scan behind a repair command.

Phase 3: Local Object Cache

- Add cache directory keyed by tenant/agent/content hash.
- On materialization, use manifest to ensure cached objects are present; fetch only misses.
- Populate temp exec tree from cache:
  - RO: symlink or hardlink immutable cache objects.
  - RW: copy/reflink selected files to avoid mutating shared cache.
- Add cache GC by total bytes, last access, and agent deletion.

Phase 4: Selective RO/RW Hydration

- Use `MountPlan.paths` to hydrate:
  - current subagent root;
  - current wake path;
  - config/tools;
  - explicit paths found in command;
  - full RO only for broad commands such as `find $RO`, `rg ... $RO`, or user-selected `ro_full`.
- Add "names-only" or "metadata-only" projection only if needed, and only for commands proven to need listings but not content.

Phase 5: Optional Virtual Filesystem Evaluation

- Re-evaluate FUSE/OverlayFS only after phases 0-4 produce data.
- Criteria for moving forward:
  - object counts make temp-tree projection a persistent bottleneck;
  - deployment environment supports safe mounts;
  - daemon lifecycle, abort, and tenant isolation are designed.
- Otherwise avoid it.

### Correctness Invariants

- Stable visible paths remain `/cortex/ro`, `/cortex/rw`, `$RO`, `$RW`.
- Backing temp paths never leak to the LLM.
- Default mode remains compatibility-first until explicitly cut over.
- RO is never writable from shell.
- RW changes are durable after successful shell completion.
- A timed-out command still persists or discards RW changes according to an explicit policy; current behavior persists after timeout if files changed before process kill, so any change must be intentional.
- Cache is an optimization, never the source of truth.
- Tenant and agent id are part of every cache namespace.
- Same-agent subagents may share RO/RW cache, but outbound identity still comes from `NOVAIC_SUBAGENT_ID`.
- Manifest mismatch falls back to safe fetch or fails closed; it must not serve stale data silently.

### Tests to Add

- Mount planner unit tests for command/profile classification.
- Compatibility tests proving default mode still matches current full RW behavior.
- Control-profile tests proving simple `agentctl` commands do not hydrate RO/RW history.
- RW durability tests for created, modified, deleted files under `rw_empty` and `rw_full`.
- Cache tests proving object GET count drops on repeated shell commands.
- Manifest repair/fallback tests.
- Timeout policy tests.
- Tenant/agent cache namespace tests.
- Subagent shared-cache tests proving shared data with distinct outbound identity.

### Follow-up Implementation Tickets

1. `T-rorw-0-metrics`: Add shell mount/materialization metrics and structured diagnostics.
2. `T-rorw-1-mount-plan`: Introduce `MountPlan` and explicit mount profiles with default-compatible behavior.
3. `T-rorw-2-control-fastpath`: Route safe CLI-only commands to `control` mode.
4. `T-rorw-3-manifest`: Add RO/RW manifest maintenance and sync estimation from manifest.
5. `T-rorw-4-cache`: Add tenant/agent local object cache and cache-backed materialization.
6. `T-rorw-5-selective-hydration`: Add explicit path and scope-based hydration.
7. `T-rorw-6-cleanup`: Remove obsolete full-sync-only assumptions and update docs/tests.

## Verification

- Checked against P001 bottlenecks:
  - full RO hydration -> addressed by mount profiles, manifest, cache, selective hydration.
  - full RW hydration -> addressed by `rw_empty`, `rw_full`, and cache-backed selected copy.
  - recursive list/get storm -> addressed by manifest and local object cache.
  - full RW stat scan -> addressed by write journal as later phase.
- Checked against P002 comparison:
  - FUSE/OverlayFS deferred as heavy substrates.
  - Hybrid cache/profile approach selected as best product fit.
- No code implementation was performed.

## Known Gaps

- Real production timing numbers are not yet captured; Phase 0 exists specifically to collect them before risky defaults change.

## Artifacts

- `novaic-cortex/novaic_cortex/sandbox.py`
- `novaic-cortex/novaic_cortex/blob_store.py`
- `.complex-problems/rorw-audit-current-path-result.md`
- `.complex-problems/rorw-optimization-options-result.md`
