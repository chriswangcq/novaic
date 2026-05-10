# Audit Live File Authority Paths Before Cutover

## Problem Definition

We need a precise map of the current live `RO` / `RW` authority path before changing package boundaries. Without this audit, later implementation could add a new LogicalFS path while registry/runtime still construct or use the old Cortex-owned store path.

## Proposed Solution

Inspect the relevant packages with pointer-style searches and targeted reads. Classify each occurrence of `CortexLogicalFileAuthority`, `CortexStore`, `BlobCortexStore`, `ws._store`, `/v1/objects`, and sandbox backing paths as active runtime path, adapter internals, test-only, docs, or stale residue. Produce a concrete implementation map and dependency boundary notes for the following child problems.

## Acceptance Criteria

- Active Workspace/runtime/API/registry construction paths are identified with file/symbol pointers.
- Direct object-store and Blob references are classified by role and removal/migration requirement.
- Tests and docs affected by the migration are listed.
- No implementation changes are made during this audit ticket.

## Verification Plan

- Run `rg` scans for the target symbols and paths.
- Read only the relevant source slices with `sed`/`nl`.
- Summarize the active path and hidden dependency risks in the result body.

## Risks

- Search terms can miss dynamically constructed imports or aliases.
- Some test helpers may look like active code unless classified carefully.

## Assumptions

- This audit is bounded enough for one execution attempt.
- Follow-up implementation tickets will close the gaps identified here.
