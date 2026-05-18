# Map LogicalFS Sandbox Blob Topology

## Problem Definition

P552 must produce a reliable current topology map for Cortex, LogicalFS, sandbox service/core, and blob service before any residue cleanup.

## Proposed Solution

Split the topology map into local module/repository inventory, concrete call/import path mapping, and test/entrypoint coverage mapping. This keeps evidence narrow and prevents broad architecture claims without file references.

## Acceptance Criteria

- Relevant modules/repos are inventoried with paths.
- Import/call paths across Cortex/LogicalFS/sandbox/blob are mapped.
- CLI/service entrypoints and tests are identified.
- Discovery commands are recorded.

## Verification Plan

Use `find`, `rg --files`, `rg` import/call searches, and targeted source reads. Parent result should cite child artifacts and avoid implementation changes.

## Risks

- Some services may be separate repositories linked by submodule or sibling checkout.
- Naming can differ from expected module names.

## Assumptions

- Local checkout is sufficient to map the currently integrated backend paths.
