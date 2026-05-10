# Move Live RO/RW Authority Into LogicalFS Boundary

## Problem Definition

The active Cortex `RO` / `RW` file path still terminates inside `novaic-cortex`: `Workspace` owns `CortexLogicalFileAuthority`, that authority owns the store adapter, and registry construction can still expose `BlobCortexStore` to live workspace assembly. This is better than scattered direct store calls, but it is not the final boundary. The final shape must make LogicalFS the live file authority and make Cortex a semantic client that supplies explicit owner/layout inputs.

## Proposed Solution

Move the active file authority abstraction into `novaic-logicalfs` as a generic, business-independent boundary. Cortex should construct or receive a LogicalFS file authority/port and use that for all live `RO` / `RW` operations. The old `CortexLogicalFileAuthority -> CortexStore` path should be physically removed from the active Cortex runtime path, not left as a parallel implementation.

The solution should be executed in smaller child problems because it crosses package boundaries:

- Define the generic LogicalFS authority contract and store adapter boundary in `novaic-logicalfs`.
- Move or replace the Blob object persistence adapter so live Workspace/registry construction no longer depends on `BlobCortexStore`.
- Refactor `novaic-cortex` Workspace, runtime, API, and registry to depend on the LogicalFS authority boundary instead of `CortexStore`.
- Delete or quarantine old Cortex-owned authority and compatibility paths.
- Strengthen guardrail tests so direct live Workspace use of `CortexStore`, `BlobCortexStore`, or object API routes fails outside the LogicalFS boundary.
- Run full backend tests and residue scans, then perform a strict `check-success` with follow-ups for any remaining bypass or compatibility branch.

## Acceptance Criteria

- `Workspace` live file methods no longer own or construct `CortexStore` / `BlobCortexStore` / object API persistence.
- LogicalFS provides the live file authority contract used by Cortex for `RO` / `RW`.
- Blob persistence is below the LogicalFS boundary and not reachable from Cortex live workspace construction except through the LogicalFS-owned adapter boundary.
- The old `novaic-cortex` in-process file authority is removed from active code or reduced to test-only code with guardrails proving it cannot be used by live runtime paths.
- Registry/runtime/API construction paths are updated so the active agent path runs through LogicalFS authority.
- Tests cover Workspace file operations, API/runtime construction, sandbox shell RO/RW behavior, and guardrail failures for direct object-store bypasses.
- Residue scans explicitly look for old direct paths, compatibility branches, stale docs, and unconnected new code.

## Verification Plan

- Inspect active construction paths with `rg` and targeted file reads before editing.
- Add or update unit tests in `novaic-logicalfs`, `novaic-cortex`, and boundary guardrail suites.
- Run package tests for `novaic-logicalfs`, `novaic-cortex`, `novaic-sandbox-service`, and the canonical backend test matrix.
- Run residue scans for `CortexLogicalFileAuthority`, `BlobCortexStore`, `CortexStore`, `/v1/objects`, direct `ws._store`, and old sandbox backing paths.
- During `check-success`, treat any active-path bypass, unconnected new implementation, stale compatibility branch, or weak test evidence as `not_success` and create a follow-up.

## Risks

- The existing `CortexStore` interface is used by tests and adapters, so removing it from live paths may require careful test helper replacement instead of blunt deletion.
- Blob persistence code may be serving both runtime and tests; moving it too quickly could create hidden fallback paths.
- A superficial refactor could leave registry/runtime still constructing the old path while tests exercise only the new path.
- Guardrails can become too broad or too narrow; they must prove the intended dependency boundary without blocking legitimate LogicalFS internals.

## Assumptions

- It is acceptable to split this ticket into child problems because the change spans LogicalFS, Cortex, Blob persistence adapter boundaries, guardrails, and tests.
- Backward compatibility is not a goal for old active runtime paths; if a migration shim is needed for tests, it must be clearly test-only or removed before closure.
- Blob remains the cheap byte/object server, LogicalFS owns realtime `RO` / `RW`, sandboxd executes processes, and Cortex owns semantic scope/workspace meaning.
