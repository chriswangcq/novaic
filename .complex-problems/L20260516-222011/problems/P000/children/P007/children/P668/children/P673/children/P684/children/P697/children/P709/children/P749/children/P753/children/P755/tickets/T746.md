# Runtime Queue Cortex service-code residue discovery ticket

## Problem Definition

Runtime, Queue, and Cortex code may still contain stale names or comments around session FSM, tool dispatch, shell output, display projection, context assembly, and workspace/file authority.

## Proposed Solution

Perform read-only scans over `novaic-agent-runtime` and `novaic-cortex` source/tests for boundary-sensitive residue. Classify hits and list exact remediation candidates.

## Acceptance Criteria

- Runtime/Queue/Cortex source and relevant tests are scanned.
- Findings are classified as current, intentional guard/test, protocol/auth encoding, or stale remediation candidate.
- Exact safe remediation candidates are listed.
- No Runtime/Queue/Cortex code is modified in this ticket.

## Verification Plan

Use targeted `rg` scans and spot-read suspicious files. Confirm this ticket records findings only and leaves patching to remediation.
