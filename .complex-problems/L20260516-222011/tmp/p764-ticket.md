# Sandbox service residue discovery ticket

## Problem Definition

Sandbox service/code may contain stale local fallback, compatibility, direct materialize/writeback, mount caching, or ownership wording that conflicts with the current Sandbox service consuming LogicalFS views and providing execution isolation.

## Proposed Solution

Scan Sandbox service, SDK, tests, scripts, and docs for residue terms, inspect representative hits, and classify each high-signal group as current execution isolation behavior, adapter boundary, stale remediation candidate, or unrelated vocabulary.

## Acceptance Criteria

- Sandbox service/source files are discovered.
- Suspicious hits are classified with file pointers.
- Remediation candidates are listed or absence is recorded.
- No product code is modified in this discovery child.

## Verification Plan

Use `rg --files` over the Sandbox service and SDK surfaces, then focused `rg` searches for fallback/compat/local/direct/materialize/writeback/mount/cache/logicalfs/blob/sandbox/raw/base64 terms. Spot-read high-signal files and run focused Sandbox tests if available.

## Risks

- Sandbox naturally contains execution, mount, process, and local path vocabulary; those terms are not automatically stale.
- The discovery child should not patch product code; remediation belongs to a later remediation branch if candidates are found.

## Assumptions

- Active Sandbox code is under `novaic-sandbox-service`, with possible SDK/client code under `novaic-sandbox-sdk` if present.
