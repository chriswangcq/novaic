# Audit LogicalFS shell integration residue

## Problem Definition

The latest production issue came from a LogicalFS adapter that still broad-mounted `/ro`. This ticket audits the Cortex/Sandbox/LogicalFS shell execution path for any similar unintegrated residue.

## Proposed Solution

Search and inspect the concrete code paths that acquire LogicalFS views, materialize snapshots, execute sandbox commands, interact with sandboxd, and read Workspace/Blob trees. Classify each broad read or fallback as live-path gap, valid explicit API, tests/docs-only, or dead residue.

## Acceptance Criteria

- Broad `/ro` materialization is either absent from live shell path or explicitly named as a remaining gap.
- Any local fallback or direct process execution bypassing sandboxd/logicalfs is identified.
- Workspace/Blob recursive reads that remain in live shell path are identified.
- Evidence points to exact files/functions.

## Verification Plan

- Use `rg` for `read_tree_bytes`, `/ro/`, `materialize`, `sandboxd`, `LocalProcessRunner`, fallback terms, and shell internal endpoint code.
- Inspect relevant slices with `sed`/`nl`.
- Re-run or cite existing targeted LogicalFS tests if needed.

## Risks

- Some broad reads are valid for runtime tool loading or tests; do not mark them as shell adapter misses.

## Assumptions

- Shell execution should be lightweight by default and broad historical reads should use explicit Cortex APIs rather than implicit mounts.
