# Service code semantic residue discovery ticket

## Problem Definition

Service code may still contain comments, wrappers, compatibility names, direct-call helpers, or tests that imply outdated ownership between Runtime, Queue, Cortex, Gateway, Business, Device, Blob, LogicalFS, Sandboxd, shell, display, VMuse, and VmControl.

## Proposed Solution

Scan service source directories and tests for boundary-sensitive terms. Classify hits as active stale code/comment, intentional protocol/auth encoding, generated/resource copy, test/fixture guard, or harmless naming. Do not patch code in this discovery step.

## Acceptance Criteria

- Service code scan covers Runtime/Queue, Cortex, Gateway/Business/Device, Blob, LogicalFS, Sandboxd, VMuse, and VmControl-relevant code.
- Findings are classified with exact file evidence.
- Safe code remediation candidates are explicit enough for the remediation child.
- No service code is modified in this discovery ticket.

## Verification Plan

Use targeted `rg` scans and spot-read suspicious files. Verify no product code was edited in this discovery ticket; record exact candidates and residual intentional hits.
