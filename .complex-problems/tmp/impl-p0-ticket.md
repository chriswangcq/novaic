# Produce Construction Plan And Boundary Map

## Problem Definition

Implementation must start from a concrete construction map rather than a vague architecture promise. The map should name storage authorities, touch points, phases, non-goals, and cleanup criteria.

## Proposed Solution

Create a Cortex architecture document that turns the prior remediation design into phased construction work.

## Acceptance Criteria

- Document exists under `docs/cortex/`.
- Document defines authority map for SQLite, LogicalFS/Workspace, Redis, Blob, and process memory.
- Document lists phases from substrate through cleanup.
- Document identifies concrete code touch points.

## Verification Plan

Read the document and verify the required sections are present. Run ledger check after result recording.

## Risks

- A document alone does not implement state authority; this is Phase 0 only.

## Assumptions

- Later phases will implement code against this plan.

