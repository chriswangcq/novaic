# Full Logical RO/RW Shell Contract Design

## Summary

Corrected design: shell must always have a complete logical `/cortex/ro` and `/cortex/rw` contract. The system must not use command-string analysis as semantic truth, because shell scripts are dynamic. Optimization should happen below the filesystem contract through mirror/cache/manifest mechanics. RW conflict frequency should be reduced by convention: subagent-private directories, a shared public directory, and per-exec tmp directories.

## Done

### 1. Corrected Principle

The visible shell contract is:

```text
/cortex/ro  = complete logical read-only agent workspace view
/cortex/rw  = complete logical writable agent workspace view
$RO         = /cortex/ro backing path for this exec
$RW         = /cortex/rw backing path for this exec
```

The shell is allowed to access RO/RW through:

- literal paths;
- environment variables;
- sourced scripts;
- generated commands;
- `eval`;
- Python/Node/Ruby/etc.;
- subprocesses.

Therefore this is invalid as a correctness mechanism:

```text
outer command string -> regex -> decide whether RO exists
```

It can remain as a compatibility/performance hint only after a safer substrate exists, but it must not define shell semantics.

Current code evidence: `novaic-cortex/novaic_cortex/sandbox.py:978-986` currently uses `_command_needs_ro(command)`. This should be treated as an optimization shortcut, not a long-term semantic boundary.

### 2. RW Directory Convention

Define the logical RW tree as:

```text
/cortex/rw/
  public/
    README.md
    artifacts/
    handoff/
    shared-state/

  subagents/
    main/
      scratch/
      artifacts/
      notes/
    <subagent-id>/
      scratch/
      artifacts/
      notes/

  tmp/
    <exec-id>/

  system/
    manifests/
    journals/
```

Meaning:

- `public/`: team-shared area. Use deliberately. Good for handoff outputs, durable artifacts, shared state.
- `subagents/<id>/`: default durable write location for each subagent.
- `tmp/<exec-id>/`: default temporary write location for a single shell execution. Can be deleted unless explicitly preserved.
- `system/`: Cortex-owned metadata/journals. Hidden by convention from normal agent work.

This is not hard isolation. Same-agent subagents are a team. The layout reduces accidental conflicts by shaping default behavior.

### 3. Injected Environment Variables

Keep current variables:

```text
RO=/cortex/ro
RW=/cortex/rw
CORTEX_RO=/cortex/ro
CORTEX_RW=/cortex/rw
CORTEX_ROOT=/cortex
NOVAIC_AGENT_ID=<agent-id>
NOVAIC_SUBAGENT_ID=<subagent-id>
NOVAIC_SCOPE_ID=<wake/root scope id>
NOVAIC_WAKE_SCOPE_PATH=<current wake path>
```

Add:

```text
RW_PUBLIC=/cortex/rw/public
RW_SELF=/cortex/rw/subagents/<safe-subagent-id>
RW_TMP=/cortex/rw/tmp/<exec-id>
RW_ARTIFACTS=/cortex/rw/subagents/<safe-subagent-id>/artifacts
RW_SCRATCH=/cortex/rw/subagents/<safe-subagent-id>/scratch
```

Optional:

```text
RW_HANDOFF=/cortex/rw/public/handoff
RW_SHARED_STATE=/cortex/rw/public/shared-state
```

Subagent id sanitization should match existing scope-id/path rules: no slash, no NUL, no `..`; unsafe characters become `-`.

### 4. Agent Behavior Protocol

Prompt/tool instructions should say:

- Write durable personal work to `$RW_SELF`.
- Write temporary files to `$RW_TMP`.
- Write user-facing or team-shared deliverables to `$RW_PUBLIC/artifacts` or `$RW_HANDOFF`.
- Do not write random files directly under `$RW`.
- Do not mutate `$RW_PUBLIC/shared-state` unless the task explicitly requires shared state.
- For reports to parent agents, prefer writing a file under `$RW_SELF/artifacts` and sending the path or summary through `agentctl im send`.

This keeps autonomy while reducing collision:

```text
default write: self
temporary write: tmp
intentional collaboration: public
```

### 5. Implementation Substrate

The target substrate is not "selective mount by command text". It is:

```text
CompleteLogicalView
  backed by PersistentAgentMirror
  validated by Manifest
  accelerated by ContentAddressedCache
  committed by WriteJournal
```

#### 5.1 PersistentAgentMirror

Maintain a per-tenant/agent local mirror inside the Cortex service runtime:

```text
cache-root/
  tenants/<user-id>/agents/<agent-id>/
    ro-mirror/
    rw-mirror/
    objects/<hash>
    manifests/
```

Before exec:

- refresh mirror from manifest/generation;
- create temp exec tree from mirror using copy/reflink/link where safe;
- expose full logical RO/RW to the command.

After exec:

- compare RW temp tree with baseline or journal;
- commit changed logical paths to CortexStore;
- update manifest and mirror.

This preserves complete view while making repeated commands cheap.

#### 5.2 Manifest

Manifest entries:

```text
logical_path
zone: ro|rw
size
content_hash or etag
mtime/generation
content_type
owner_hint: public|subagent:<id>|system
```

Manifest is source of sync planning, not source of truth. CortexStore remains source of truth.

#### 5.3 ContentAddressedCache

Objects keyed by content hash:

```text
objects/sha256/<hash>
```

- RO files can link to immutable cache objects.
- RW files should copy/reflink from cache into temp tree, not hardlink mutable shared files.
- Cache can be shared among same-agent subagents.
- Cache must be namespaced by tenant and agent at directory/root level.

#### 5.4 WriteJournal

Phase 1 can keep current recursive before/after RW stat scan. Later:

- Track known changed paths.
- Track deletes/tombstones.
- Commit only changed files.
- Leave conflict protocol out of scope for now.

### 6. Staged Plan

#### Phase 0: Contract and Prompt Update

- Add docs and prompt text for `$RW_SELF`, `$RW_PUBLIC`, `$RW_TMP`.
- Add env injection for the new variables.
- Ensure directories exist in each exec tree.
- Keep current full materialization behavior.

#### Phase 1: Metrics Before Behavior Change

Add metrics/logging:

- command id / exec id;
- RO object count;
- RW object count;
- bytes downloaded;
- bytes uploaded;
- materialization duration;
- process duration;
- RW scan duration;
- commit duration;
- tmp cleanup count;
- public write count;
- self write count.

No semantic change.

#### Phase 2: Persistent Mirror Without Semantic Change

- Create per-agent mirror.
- Populate mirror from CortexStore.
- Use mirror to build temp exec tree.
- Keep full logical RO/RW visible.
- Fall back to direct BlobStore fetch if mirror is missing/corrupt.

#### Phase 3: Manifest Delta Refresh

- Maintain manifests on workspace writes, scope writes, payload writes, deletes, archive moves.
- Refresh mirror by manifest delta rather than recursive full list/get.
- Add repair command to rebuild manifest from CortexStore.

#### Phase 4: Faster RW Commit

- Keep compatibility but optimize changed path detection.
- Introduce write journal or filesystem event tracking if practical.
- Do not add concurrency protocol yet.

#### Phase 5: Optional FUSE Evaluation

Only revisit FUSE if:

- mirror + manifest + cache still fails performance goals;
- deployment can support user-space filesystem safely;
- abort/deadlock handling is designed;
- observability is strong.

### 7. Invariants

- `/cortex/ro` and `/cortex/rw` always exist for shell.
- The logical visible tree is complete for the selected agent.
- Optimization cannot make a valid file disappear.
- Command-string regex cannot be the semantic source of RO/RW visibility.
- RO remains read-only from the logical contract.
- RW writes are persisted after exec according to existing shell completion policy.
- `$RW_TMP` is not durable unless explicitly promoted.
- Same-agent subagents share workspace by design.
- Outbound identity is still `NOVAIC_SUBAGENT_ID`.
- Cache/mirror corruption must degrade to safe rebuild or fail closed, not stale success.

### 8. Non-goals

- No hard ACL isolation between subagents.
- No full concurrent write protocol in this phase.
- No immediate FUSE implementation.
- No command-string semantic prediction.
- No automatic merge of conflicting public writes.

### 9. Tests

Add tests for:

- env injection:
  - `$RW_PUBLIC`
  - `$RW_SELF`
  - `$RW_TMP`
  - `$RW_ARTIFACTS`
  - `$RW_SCRATCH`
- path sanitization for subagent ids.
- default directories exist.
- writing to `$RW_SELF` persists.
- writing to `$RW_PUBLIC` persists.
- writing to `$RW_TMP` follows tmp retention policy.
- same-agent different subagents get distinct `$RW_SELF`.
- both subagents can read `$RW_PUBLIC`.
- shell script hidden access to `$RO` works even if outer command string does not contain `$RO`.
- mirror/cache mode preserves full logical view.
- manifest mismatch triggers repair/fallback.

### 10. Follow-up Tickets

- `T-rorw-contract-env`: Add RW directory convention env variables and prompt docs.
- `T-rorw-tmp-policy`: Define and implement `$RW_TMP` lifecycle.
- `T-rorw-metrics`: Add materialization and commit metrics.
- `T-rorw-mirror`: Build per-agent persistent mirror without behavior change.
- `T-rorw-manifest`: Add manifest delta refresh and repair.
- `T-rorw-cache`: Add content-addressed cache under mirror.
- `T-rorw-journal`: Optimize RW commit path with write journal.
- `T-rorw-remove-command-semantic-gating`: Remove or demote `_command_needs_ro` from semantic role once complete view substrate exists.

## Verification

- Cross-checked against current code:
  - `_command_needs_ro` currently exists at `novaic-cortex/novaic_cortex/sandbox.py:978-986`; design demotes this from semantic boundary.
  - `_materialize_workspace` currently full-copies selected prefixes at `novaic-cortex/novaic_cortex/sandbox.py:1057-1093`; design replaces repeated download with mirror/manifest/cache.
  - shell exec creates temp trees and injects env at `novaic-cortex/novaic_cortex/sandbox.py:1135-1181`; design keeps this visible contract and adds env variables.
  - RW before/after scan and persistence happen at `novaic-cortex/novaic_cortex/sandbox.py:1231-1233`; design keeps it initially and later replaces with journal.
- No code implementation was performed.

## Known Gaps

- none for the design pass.
- Implementation, benchmarking, and deployment are follow-up work.

## Artifacts

- `.complex-problems/rorw-full-logical-view-design-root.md`
- `.complex-problems/rorw-full-logical-view-design-ticket.md`
- `novaic-cortex/novaic_cortex/sandbox.py`
