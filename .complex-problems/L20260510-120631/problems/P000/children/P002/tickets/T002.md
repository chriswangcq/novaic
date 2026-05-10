# Ticket: Migrate Cortex LogicalFS Adapter

## Problem Definition

`novaic-cortex/novaic_cortex/logical_fs.py` still contains generic filesystem substrate logic: materializing `/ro` and `/rw`, tracking file stats, calculating RW diffs, resolving stable cwd, and sanitizing backing paths. This keeps Cortex partially responsible for LogicalFS mechanics and makes the boundary look like a half-extraction.

The intended final shape is:

- `novaic-logicalfs` owns generic snapshot -> view materialization and view -> patch observation.
- Cortex owns semantic projection from Cortex Workspace to `LogicalFSSnapshot`, explicit shell/env/subagent layout, capability-bin generation, and applying `LogicalFSPatch` back to Workspace.
- sandboxd/sandbox_core remain process-execution infrastructure and do not own Cortex semantics.

## Proposed Solution

Refactor the Cortex LogicalFS adapter so it imports and delegates generic file-view behavior to `logicalfs`.

Keep Cortex-local code only for:

- Reading Cortex Workspace `/ro` and `/rw` entries into `LogicalFSSnapshot`.
- Building explicit `LogicalFSLayout`/`LogicalFSEnv` from request inputs and Cortex runtime state.
- Installing shell capability scripts into the materialized view.
- Translating `LogicalFSPatch` back into Workspace writes/deletes.
- Returning Cortex-facing changed paths and sandbox bind/cwd information.

Remove duplicate generic helpers from Cortex once their behavior is provided by `novaic-logicalfs`.

## Acceptance Criteria

- `novaic_cortex.logical_fs` delegates materialization, cwd resolution, path sanitization, and RW diff detection to `logicalfs`.
- `novaic-logicalfs` has no dependency on Cortex, sandboxd, agent runtime, business code, or agent identity.
- Cortex still provides stable `/cortex/ro`, `/cortex/rw`, `/cortex/bin` shell view and explicit env.
- Shell capability scripts still work through the adapter boundary.
- Existing Cortex sandbox tests pass with `novaic-logicalfs` on `PYTHONPATH`.
- No old generic duplicate implementation remains in Cortex.

## Verification Plan

- Run focused `logicalfs` tests.
- Run focused Cortex sandbox tests that exercise mount namespace wiring and RW changed-path reporting.
- Scan for forbidden imports from `novaic-logicalfs` into product/service modules.
- Scan `novaic-cortex/novaic_cortex/logical_fs.py` for displaced generic helper names.

## Risks

- Capability-bin generation is Cortex-specific and must stay outside the generic LogicalFS package.
- Existing tests may assert `/rw/...` changed-path output while generic patch paths use `/cortex/rw/...`; Cortex adapter must translate explicitly.
- Workspace deletion semantics need to stay identical for RW files removed during shell execution.

## Assumptions

- LogicalFS is a substrate package, not a server yet.
- Service/server extraction, deploy wiring, and full residue cleanup are covered by later tickets P003/P004.
