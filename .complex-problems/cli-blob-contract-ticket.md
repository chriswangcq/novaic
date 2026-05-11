# Split CLI blob contract remediation by command surface

## Problem Definition

The root problem spans multiple shell-exposed CLIs and output classes. A safe fix needs to inventory all CLI surfaces, repair artifact-producing commands, and verify that old base64/stdout contracts are gone from live paths.

## Proposed Solution

Split the work into focused child problems:

- Inventory all shell capability CLIs and classify their outputs.
- Fix `devicectl hd` artifact-producing commands, especially screenshot and file transfer paths.
- Audit/fix `agentctl` and `cortex` CLI outputs so they do not emit large binary/base64 payloads as primary stdout.
- Add/adjust tests for blob artifact contract and remove or mark old incompatible expectations.
- Run focused and broader verification, then record residual risks.

## Acceptance Criteria

- Child problems cover every live shell CLI command surface.
- Artifact-producing commands are repaired on active paths.
- Tests cover the repaired contract.
- Final check maps each root criterion to evidence.

## Verification Plan

- Use `rg`, code inspection, and tests to inventory command surfaces.
- Run targeted tests for shell capabilities, tool output projection, runtime shell wrapper, and Cortex payload handling.
- Run broader project tests where feasible for touched repos.

## Risks

- Some CLIs may be proxy surfaces over external services; changing output shape may require compatibility handling.
- Existing tests may encode old stdout/base64 behavior.
- Device-backed paths may be hard to fully end-to-end test locally; unit/contract tests must cover the transformation boundary.

## Assumptions

- `tool-output.v1` is the canonical shell output contract for structured CLI results.
- Blob service is the correct storage boundary for media/file artifacts.
