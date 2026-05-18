# Ticket: Verify Cortex Archive Diagnostics Persistence

## Problem Definition

After propagation and persistence changes, verify the aggregate runtime/Cortex archive diagnostics contract and scan for residue.

## Proposed Solution

Run focused runtime and Cortex suites together. Run source searches for `archive_diagnostics`, `scope_end`, `session_generation`, `finalize_reason`, and `remaining_stack` to ensure diagnostic data is nested and top-level semantic stack remains list-shaped.

## Acceptance Criteria

- Focused runtime/Cortex tests pass after all changes.
- Source search confirms no active-generation synthesis was added for Cortex archive diagnostics.
- Source search confirms diagnostic `remaining_stack` is nested under `archive_diagnostics`, not replacing semantic `remaining_stack`.
- Any gap discovered is either fixed or split into a follow-up.

## Verification Plan

- Run runtime focused suite from P372.
- Run Cortex focused suite from P376.
- Run source residue scans.

