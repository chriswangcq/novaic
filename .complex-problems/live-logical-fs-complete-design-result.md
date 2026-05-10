# Live LogicalFS Complete Design Result

## Summary

The complete solution is a live Cortex LogicalFS service, not a temp projection optimizer. Shell processes should run against a real live `/cortex` filesystem view. File semantics live in LogicalFS; SandboxExec is only a generic process runner. There is no `commit` concept in Sandbox or ShellOrchestrator: writes are handled as filesystem operations when they happen, journaled by LogicalFS, and synced to Blob/OSS by LogicalFS workers.

## Done

### 1. Final Mental Model

```text
Blob/OSS
  = durable byte/object backend

Cortex LogicalFS
  = live filesystem provider
  = path semantics + metadata + journal + cache + blob sync

ShellExecutionOrchestrator
  = lifecycle coordinator
  = acquire live view, build generic process spec, release live view reference

SandboxExec
  = generic process runner
  = cwd/env/stdout/stderr/timeout/kill only

Agent Runtime
  = passes identity and asks for shell execution
```

The final shell flow:

```text
Runtime shell tool
  -> ShellExecutionOrchestrator.execute(identity, command)
  -> LogicalFS.acquire_view(identity, exec_id)
  -> SandboxExec.run(ProcessSpec)
  -> LogicalFS.release_view(view_ref)
  -> ShellResult
```

Important: `release_view` is not `commit`. It is reference cleanup, tmp lifecycle, and resource accounting. Writes were already observed and journaled by LogicalFS.

### 2. Component Boundaries

#### LogicalFS owns

- `/cortex/ro` and `/cortex/rw` logical namespace.
- Full logical filesystem visibility.
- File metadata:
  - type;
  - size;
  - mode;
  - mtime/ctime;
  - generation;
  - owner hints;
  - dirty/sync status.
- Read/write/open/create/truncate/rename/unlink/mkdir/rmdir/readdir/stat.
- RW directory convention:
  - `public`;
  - `subagents/<id>`;
  - `tmp/<exec-id>`;
  - `system`.
- Write journal / WAL.
- Content-addressed local cache.
- Persistent mirror.
- Manifest.
- Blob/OSS sync.
- Crash recovery.
- GC.
- Repair/rebuild.
- Mount lifecycle.

#### SandboxExec owns

- Execute process with given `ProcessSpec`.
- Handle timeout and kill.
- Capture stdout/stderr.
- Return exit code and duration.
- It does not know RO/RW, Blob, cache, manifest, journal, commit, or paths beyond cwd/env in `ProcessSpec`.

#### ShellExecutionOrchestrator owns

- Call `LogicalFS.acquire_view`.
- Convert view to generic `ProcessSpec`.
- Call `SandboxExec.run`.
- Call `LogicalFS.release_view`.
- Merge process result and filesystem diagnostics.
- It does not decide file sync, changed paths, or commits.

#### Blob/OSS owns

- Object get/put/delete/list.
- Optional object metadata/etag.
- It is not a filesystem.

### 3. Why Temp Projection + Commit Is Not Final

The current code creates a temp directory per shell exec, copies RO/RW into it, runs a process, scans RW, then persists changed files. That model forces a `commit` concept because writes happen outside the authoritative FS layer.

The complete model removes this:

```text
old:
  copy workspace -> run shell -> diff temp tree -> commit

new:
  shell writes LogicalFS directly
  LogicalFS journals/syncs live
```

So the final architecture must delete or retire:

- command-string semantic mount decisions;
- command rewrite as the only `/cortex` path support;
- post-process RW diff as the authoritative change detector;
- Sandbox-owned persistence logic.

### 4. Full Logical `/cortex` Mount

The shell must see actual stable paths, not only rewritten command text:

```text
/cortex/ro
/cortex/rw
```

This matters because scripts can contain literal `/cortex/ro` paths hidden from the outer command string.

Complete target:

- Use a process mount namespace or equivalent sandbox wrapper.
- Mount or bind a LogicalFS-provided `/cortex` into that namespace.
- `RO`, `RW`, `CORTEX_RO`, `CORTEX_RW`, `CORTEX_ROOT` point to real visible paths.
- No command string rewrite is needed for correctness.
- Output path sanitization may remain to keep implementation paths out of monitor output.

### 5. Substrate Choice

There are three possible substrates:

#### A. FUSE-backed LogicalFS: final complete target

Every file operation enters LogicalFS:

```text
open/read/write/rename/delete/readdir/stat/fsync
  -> LogicalFS daemon
  -> local metadata/cache/journal
  -> background Blob sync
```

Pros:

- Most semantically complete.
- No post-run commit.
- True hidden script access works.
- Read/write behavior is centralized.
- Future features like lazy RO reads and live sync are natural.

Cons:

- Daemon lifecycle.
- Mount permissions/capabilities.
- Deadlock/abort handling.
- More operational surface.

Verdict: this is the correct complete target, but it must be implemented with very strong observability and recovery.

#### B. Persistent mirror + watcher: transitional only

Shell writes a normal local directory; watcher records changes.

Pros:

- Easier to start.
- No FUSE dependency.

Cons:

- Watcher can miss events.
- Rename/crash recovery is messy.
- LogicalFS sees changes after kernel writes, not as the operation owner.

Verdict: acceptable as an intermediate stepping stone, not final.

#### C. Temp projection + diff: current fallback

Pros:

- Simple.
- Easy cleanup.

Cons:

- Slow.
- Needs commit/diff.
- Cannot provide actual `/cortex` semantics for hidden script access unless using real mount/chroot.

Verdict: fallback only; not final.

### 6. LogicalFS Data Model

#### Metadata Store

Use SQLite or another durable local metadata DB inside Cortex service runtime:

```text
logical_nodes(
  tenant_id,
  agent_id,
  logical_path,
  zone,                 -- ro|rw
  node_type,            -- file|dir|symlink
  mode,
  size,
  content_hash,
  generation,
  mtime_ns,
  ctime_ns,
  owner_hint,           -- public|subagent:<id>|system|tmp:<exec-id>
  sync_state,           -- clean|dirty|syncing|failed|local_only
  deleted
)

journal_entries(
  journal_id,
  tenant_id,
  agent_id,
  op,                   -- create|write|truncate|rename|unlink|mkdir|rmdir|chmod|fsync
  logical_path,
  dst_path,
  content_hash,
  generation,
  exec_id,
  subagent_id,
  created_at,
  applied_local,
  synced_remote
)

sync_queue(
  journal_id,
  priority,
  attempts,
  next_attempt_at,
  last_error
)
```

#### Content Store

```text
logicalfs-cache/
  tenants/<tenant-id>/agents/<agent-id>/
    objects/sha256/<hash>
    staging/<exec-id>/
    mounts/
    manifests/
```

RO and RW file bytes are content-addressed locally. Blob/OSS is remote persistence and cross-process recovery source.

### 7. Read Semantics

For `/cortex/ro`:

- RO metadata comes from Cortex scope/config/payload source of truth.
- Reads are cache-first.
- Cache miss fetches from Blob/OSS.
- RO mutation returns permission error.
- RO generation advances when Cortex writes scopes, steps, payloads, config, or archives.

For `/cortex/rw`:

- Reads see latest local LogicalFS state.
- Dirty local writes are visible immediately to later reads and subsequent shell execs.
- If a path is clean and not cached, fetch from Blob.

### 8. Write Semantics

For `/cortex/rw`:

1. File operation enters LogicalFS.
2. LogicalFS validates path and ownership convention.
3. LogicalFS writes data to local content/staging.
4. LogicalFS appends journal entry.
5. LogicalFS updates local metadata generation.
6. Operation returns success to process.
7. Background sync worker uploads content and metadata to Blob/OSS.
8. Sync state moves `dirty -> syncing -> clean`, or `failed` with retry.

No Sandbox commit exists.

Durability policy should be explicit:

```text
journal_ack: syscall returns after local durable journal + data staging
blob_ack: fsync or selected operations wait for Blob sync
```

Recommended default:

- normal writes: `journal_ack`;
- explicit `fsync`: can wait for local journal durability;
- critical artifacts may request `blob_ack` through a CLI or metadata command later.

### 9. Rename/Delete Semantics

Rename:

- Atomic in LogicalFS metadata.
- Journal records source and destination.
- Blob sync can implement as copy/delete or backend move.
- Readers see new path immediately after metadata update.

Delete:

- Tombstone metadata locally.
- Journal delete.
- Background delete in Blob.
- Cache object may remain until GC if content-addressed.

### 10. Tmp Semantics

`/cortex/rw/tmp/<exec-id>`:

- Live filesystem path.
- Default `local_only`.
- Not synced to Blob unless promoted.
- Deleted on `release_view`, TTL expiry, or agent cleanup.
- If process times out, tmp cleanup policy still applies.

Promotion:

```bash
mv "$RW_TMP/result.json" "$RW_SELF/artifacts/result.json"
```

Once moved outside tmp, normal RW sync applies.

### 11. RW Layout

```text
/cortex/rw/
  public/
    artifacts/
    handoff/
    shared-state/

  subagents/
    <safe-subagent-id>/
      scratch/
      artifacts/
      notes/

  tmp/
    <exec-id>/

  system/
    manifests/
    journals/
```

Injected env:

```text
RW_PUBLIC=/cortex/rw/public
RW_SELF=/cortex/rw/subagents/<safe-subagent-id>
RW_TMP=/cortex/rw/tmp/<exec-id>
RW_ARTIFACTS=/cortex/rw/subagents/<safe-subagent-id>/artifacts
RW_SCRATCH=/cortex/rw/subagents/<safe-subagent-id>/scratch
```

Behavior convention:

- Default write -> `$RW_SELF`.
- Temporary write -> `$RW_TMP`.
- Shared write -> `$RW_PUBLIC`.
- Handoff -> `$RW_PUBLIC/handoff`.

### 12. Mount/View Model

`LogicalFS.acquire_view(identity, exec_id)` returns:

```python
LiveFSView(
    exec_id=...,
    tenant_id=...,
    agent_id=...,
    subagent_id=...,
    mount_root="/cortex" or namespace mount point,
    env={
        "RO": "/cortex/ro",
        "RW": "/cortex/rw",
        ...
    },
    cwd="/cortex/rw/subagents/<id>",
    cleanup_policy=...
)
```

`release_view(view_ref)`:

- decrements refcount;
- cleans tmp if policy says so;
- records metrics;
- does not commit.

### 13. Crash Recovery

On LogicalFS service start:

1. Load metadata DB.
2. Replay unapplied journal entries.
3. Reconstruct sync queue for dirty/failed entries.
4. Validate content-addressed objects referenced by metadata.
5. Rebuild missing cache objects from Blob when possible.
6. Mark inconsistent entries for repair.
7. Expose health:
   - `clean`;
   - `recovering`;
   - `degraded`;
   - `blocked`.

Recovery commands:

```text
logicalfs repair-manifest --agent <id>
logicalfs rebuild-cache --agent <id>
logicalfs sync-status --agent <id>
logicalfs gc --agent <id>
```

### 14. Blob/OSS Sync

Blob layout can remain object-key based:

```text
agents/<agent-id>/ro/...
agents/<agent-id>/rw/...
```

But LogicalFS should internally prefer content-addressed local storage plus manifest metadata. Remote object writes may remain path-keyed initially for compatibility, then optionally evolve.

Sync worker:

- consumes `sync_queue`;
- batches small writes when safe;
- uploads content;
- writes remote metadata/manifest if supported;
- marks journal synced;
- retries with backoff;
- emits metrics.

### 15. Observability

Metrics:

- `logicalfs_ops_total{op,zone,result}`
- `logicalfs_op_latency_ms{op,zone}`
- `logicalfs_cache_hits_total`
- `logicalfs_cache_misses_total`
- `logicalfs_dirty_entries`
- `logicalfs_sync_queue_depth`
- `logicalfs_sync_failures_total`
- `logicalfs_recovery_duration_ms`
- `logicalfs_mount_refcount`
- `logicalfs_tmp_bytes`
- `logicalfs_public_writes_total`
- `logicalfs_self_writes_total`

Agent monitor should show:

- shell process duration;
- filesystem dirty/sync status;
- tmp cleanup status;
- any sync failures as infra warnings, not hidden in stdout.

### 16. Security and Identity

Tenant and agent are the hard storage namespace.

Same-agent subagents share workspace by design. Subagent id affects:

- `$RW_SELF`;
- `$RW_TMP`;
- write owner hints;
- audit log;
- outbound IM identity.

No hard ACL between same-agent subagents in this phase.

### 17. Implementation Phases

#### Phase 0: Contracts Only

- Add docs and prompt updates for RW layout.
- Add env variable design.
- Add tests as pending design references.
- No behavior change.

#### Phase 1: Extract Process Runner Boundary

- Split current `Sandbox` into:
  - `SandboxExec` generic process runner;
  - legacy temp projection adapter.
- Keep old behavior behind adapter.
- This prepares for live FS without changing semantics.

#### Phase 2: LogicalFS Metadata and Journal

- Add LogicalFS service/classes with metadata DB and journal.
- No FUSE yet.
- Unit test operations in memory/local disk.

#### Phase 3: RW Directory Convention in Current Projection

- Inject `$RW_SELF`, `$RW_PUBLIC`, `$RW_TMP`.
- Ensure dirs exist.
- Update prompt defaults.
- This is useful immediately and low risk.

#### Phase 4: Live RW Mirror Transitional Mode

- Use persistent local mirror for RW.
- Optional watcher/journal bridge.
- Still not final, but begins removing repeated RW materialization.
- Keep fallback to temp projection.

#### Phase 5: FUSE-backed Live `/cortex`

- Implement FUSE daemon for `/cortex/ro` and `/cortex/rw`.
- Route reads/writes through LogicalFS.
- Mount into shell process namespace.
- Keep legacy projection as fallback.

#### Phase 6: Blob Sync Worker and Recovery

- Add background sync queue.
- Add crash recovery.
- Add repair and GC commands.
- Add monitor visibility.

#### Phase 7: Cutover and Cleanup

- Enable live FS per agent/runtime config.
- Shadow compare with old projection where practical.
- Remove command-string semantic RO gating.
- Retire temp projection commit/diff from default path.
- Keep emergency fallback for one release window, then delete.

### 18. Test Plan

Boundary tests:

- SandboxExec has no import/dependency on LogicalFS internals.
- LogicalFS has no dependency on shell process execution.
- ShellOrchestrator is thin and owns no file semantics.

Filesystem tests:

- hidden script literal `/cortex/ro` access works.
- `$RO` and literal `/cortex/ro` both work.
- write to `$RW_SELF` visible in later exec immediately.
- write to `$RW_PUBLIC` visible to another subagent.
- write to `$RW_TMP` cleaned by policy.
- rename is atomic from reader perspective.
- delete creates tombstone and later syncs remote delete.
- RO write fails.
- crash recovery replays dirty journal.
- sync failure does not lose local file.
- Blob sync eventually marks clean.
- cache miss fetches content.
- cache corruption triggers repair/fallback.

Performance tests:

- repeated `agentctl im read` does not list/download full RO/RW.
- repeated shell reads hit local cache.
- large historical RO does not block simple shell command startup after live mount warmup.

### 19. Non-goals

- No hard ACL isolation among same-agent subagents.
- No distributed multi-writer conflict resolution in this pass.
- No automatic semantic interpretation of shell command strings.
- No direct Blob-as-filesystem exposure.
- No requirement that every write waits for remote Blob before returning.

## Verification

- Checked against current code:
  - Current `_command_needs_ro` at `novaic-cortex/novaic_cortex/sandbox.py:978-986` is incompatible as a final semantic boundary.
  - Current `_materialize_workspace` at `novaic-cortex/novaic_cortex/sandbox.py:1057-1093` is a temp projection implementation, not live FS.
  - Current env/path setup at `novaic-cortex/novaic_cortex/sandbox.py:1135-1181` can inspire `ProcessSpec`, but final design should expose actual `/cortex`, not rely on command rewrite.
  - Current RW scan/persist at `novaic-cortex/novaic_cortex/sandbox.py:1231-1233` should be retired from final default path.
- Cross-checked against the prior corrected design in `.complex-problems/rorw-full-logical-view-design-result.md`.
- No code implementation was performed.

## Known Gaps

- none for this design pass.
- Implementation requires follow-up tickets and careful staged migration.

## Artifacts

- `.complex-problems/live-logical-fs-complete-design-root.md`
- `.complex-problems/live-logical-fs-complete-design-ticket.md`
- `.complex-problems/rorw-full-logical-view-design-result.md`
- `novaic-cortex/novaic_cortex/sandbox.py`
