# Design Blob Payload Authority Contract

## Problem Definition

Blob stores large raw payload bytes. This is acceptable only if Blob is never treated as semantic truth. The system needs an explicit manifest and lifecycle rule.

## Proposed Solution

Keep Blob for raw bytes, but store semantic manifests and lifecycle references in SQLite/Workspace.

## Acceptance Criteria

- Define what Blob owns and what it does not own.
- Define payload manifest fields and lifecycle.
- Define missing/corrupt blob behavior.
- Include cleanup/retention verification.

## Verification Plan

Check the contract against payload upload, fetch, missing blob, hash mismatch, retention, and display/download workflows.

## Risks

- Overloading SQLite with raw bytes would make it slow.
- Keeping only Blob refs without manifest would leave lifecycle ambiguous.

## Assumptions

- Blob remains the cheap file server for raw bytes.

