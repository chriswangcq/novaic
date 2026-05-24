# LogicalFS RO/RW Realtime File Authority

## Decision

LogicalFS is the file-operation and view authority for Cortex/shell realtime
`RO` / `RW` views. Cortex remains the semantic owner of agent, wake, scope,
step, payload, and workspace meaning. Blob Service is the cheap file server for
durable bytes and does not need realtime semantics.

Blob Service owns durable bytes, object storage primitives, multipart upload,
and blob references. Display and artifacts still use Blob for byte storage and
delivery. The rule is narrower and sharper: every Cortex-related shell/workspace
file operation that depends on live `RO` / `RW` semantics must go through
LogicalFS. Other ordinary files can stay Blob-backed without pretending to be a
live filesystem.

## Current Gap

The current code is close to the target shape, with remaining cleanup focused on
service extraction and hardening:

- Blob Service exposes base byte/blob APIs and object-tree primitives used by
  infrastructure.
- LogicalFS owns the live file authority and may use a Blob object adapter below
  that boundary.
- Cortex owns Workspace semantics and uses a LogicalFS authority for file-like
  Workspace APIs.
- Cortex uses the `novaic-logicalfs` substrate as a library to materialize a
  snapshot into a sandbox mount, then writes RW patches back to Workspace.
- Sandboxd only executes a process over the materialized view.

This is improved, but LogicalFS is not yet a standalone service boundary. The
remaining risk is future code reintroducing direct live workspace paths around
Blob object APIs, Cortex-local file authority wrappers, or sandbox scratch state.

## Target Model

```text
Cortex / Runtime shell pipeline
  scope/workspace semantics and shell orchestration
        |
        | live RO/RW file intents
        v
LogicalFS
  realtime RO/RW file-operation and namespace authority
  RO/RW layout, subagent RW layout, snapshots, patches, stable shell paths
        |
        | store/load RO/RW bytes
        v
Blob Service
  cheap file server: blob refs, object primitives, multipart, physical backend
        |
        v
Disk / OSS / S3

App, CLI, display, and artifact byte delivery can use Blob directly when they
do not need live Cortex/shell RO/RW semantics.
```

Sandboxd is not a file authority. It receives an executable filesystem view
from LogicalFS, runs a process, and reports process output. It may host the
local mount implementation, but it should not own workspace semantics,
subagent semantics, display semantics, or blob persistence rules.

## Responsibilities

### Blob Service

Owns:

- raw bytes and blob references
- object storage primitives used by infrastructure
- multipart upload lifecycle
- physical backend choice such as disk, OSS, or S3
- byte-level metadata and limits
- display bytes and artifact bytes, when represented as Blob objects

Does not own:

- `/ro` and `/rw` semantics
- agent, wake, scope, or subagent layout
- shell cwd/env rules
- realtime RO/RW diffs or file-view authorization
- display/artifact product meaning

### LogicalFS Service

Owns:

- realtime `RO` / `RW` namespace APIs
- stable path layout such as `/cortex/ro`, `/cortex/rw`, and subagent RW dirs
- RO/RW projection rules
- file read/write/list/delete/move semantics above Blob
- snapshot and patch semantics for shell execution
- live update propagation for RO/RW state when needed
- mapping from explicit Cortex owner metadata to durable Blob object keys

Does not own:

- LLM prompt/context decisions
- Cortex scope lifecycle state
- Queue/session FSM state
- raw Blob physical backend configuration
- process execution

### Cortex

Owns:

- agent-root, wake, skill, scope, step, payload, and context semantics
- which files belong in RO vs RW for a given agent/session/subagent
- context assembly and tool contract semantics

Uses LogicalFS for:

- Workspace file persistence and listing
- exposing `/ro` and `/rw` to shell
- reading payload-backed files when they are filesystem entries

### Sandboxd

Owns:

- process execution
- timeout and process result capture
- bind/mount namespace mechanics when needed

Uses LogicalFS for:

- executable filesystem views
- stable path mount inputs
- post-run patch collection, if the local implementation stays colocated

## Hard Boundary Rules

1. Cortex-related shell/workspace files must not bypass LogicalFS for live
   `RO` / `RW` semantics.
2. Direct Blob access is allowed for cheap file serving, base byte/blob
   functions, attachments, display bytes, artifact bytes, and LogicalFS
   internals implementing persistence.
3. Cortex may own semantic names, but LogicalFS must own file operations.
4. Sandboxd may execute over a view, but LogicalFS must own the view contract.
5. Display and artifacts use Blob for bytes. If the source starts as an RO/RW
   file, that file must be copied/exported through Blob before display or
   download. LogicalFS does not provide display/download handles.
6. Tests and CI should reject new direct Blob-object live RO/RW file paths
   outside LogicalFS internals.

## Migration Shape

### Phase 1: Declare the Boundary

- Keep Blob Service as the cheap bytes/object file server.
- Document LogicalFS as the Cortex/shell RO/RW authority.
- Add guardrails that distinguish base Blob use from live RO/RW semantics.

### Phase 2: Promote LogicalFS From Library To Service Boundary

- Define LogicalFS HTTP or RPC contracts focused on RO/RW:
  - `read`, `write`, `list`, `delete`, `move`
  - `snapshot`
  - `apply_patch`
- Keep the existing local substrate as an implementation detail behind the
  service boundary.

### Phase 3: Move Cortex Workspace Persistence Behind LogicalFS

- Replace Cortex-local persistence adapters with a LogicalFS-backed workspace
  adapter.
- Cortex passes semantic owner/scope/session/subagent metadata explicitly.
- LogicalFS maps those semantics to durable Blob object keys.

### Phase 4: Move Shell/Sandbox Mounts Behind LogicalFS

- Sandbox execution requests reference a LogicalFS view id or snapshot id.
- Sandboxd no longer receives Cortex Workspace details.
- Patch application becomes LogicalFS responsibility, not Cortex glue code.

### Phase 5: Display And Artifact Bytes

- `display` keeps direct Blob support for base `blob://...` files.
- Artifacts are Blob-backed when they need display/download.
- RO/RW files that need display/download are first exported or copied to Blob.
- LogicalFS remains a live RO/RW layer; it does not become a display/download
  handle service.

### Phase 6: Delete Old Paths

- Remove direct live RO/RW file use of Blob object APIs outside LogicalFS.
- Remove Cortex-local live RO/RW file service wrappers.
- Remove sandbox-local file semantics.
- Add residue scans for accidental direct Blob object calls in live RO/RW paths.

## Acceptance Criteria

- There is exactly one Cortex/shell live `RO` / `RW` authority: LogicalFS.
- Blob remains a cheap file server and byte/object infrastructure.
- Cortex no longer directly implements live RO/RW persistence over Blob.
- Sandboxd no longer owns workspace or subagent file semantics.
- Display path is split cleanly:
  - base attachments: direct Blob
  - ordinary artifact/display bytes: direct Blob
  - RO/RW file operations and views: LogicalFS only
  - RO/RW file display/download: export/copy to Blob, then display/download
- New tests prove Cortex/shell live RO/RW paths cannot bypass LogicalFS.
