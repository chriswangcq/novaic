# Classify Cortex Materialize API Residue

## Problem Definition

P566 must classify Cortex materialization and direct file access hits, especially `Workspace.materialize()`, to decide whether they are intended or remediation candidates.

## Proposed Solution

Run targeted scans over `novaic-cortex/novaic_cortex`, read relevant code slices, classify each hit bucket, and record remediation candidates for P554 if any.

## Acceptance Criteria

- Scan commands and outputs are recorded.
- `Workspace.materialize()` is explicitly classified.
- Direct `_files` access and `/rw/scratch` writes are classified.
- Any risky residue is called out for P554.

## Verification Plan

Use `rg` scans and line-numbered reads, then artifact existence/anchor checks.

## Risks

- Direct `_files` access is normal inside `Workspace`; classification must avoid false positives.
- `materialize` can be generic terminology rather than an active fallback.

## Assumptions

- Production Cortex code lives under `novaic-cortex/novaic_cortex`.
