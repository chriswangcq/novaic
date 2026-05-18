# Finalize Recovery Ownership Map

## Problem Definition

P507 must map finalize/watchdog/recovery paths with file references and ownership labels, without changing production code.

## Proposed Solution

Use targeted searches and bounded source slices to map normal wake finalize, session-ended handling, saga compensation, suspected-dead recording, recovery archive outbox, recovery wake restart, and remaining-stack semantics. Save raw guard output and an ownership matrix.

## Acceptance Criteria

- The map cites concrete file references for each path.
- Each path has an explicit owner classification.
- Ambiguous or multi-owner candidates are listed for P508.
- No production code is modified.

## Verification Plan

Save targeted guard outputs, inspect bounded slices for the core files, write an ownership matrix, and record whether any remediation candidate exists.

## Risks

- Recovery terms can look like bypasses even when they are required compensation paths.

## Assumptions

- P508 will handle any active gap found by this mapping child.
