# Replace stale device-screenshot artifact namespace fixtures

## Problem Definition

Some tool-output tests still use `blob://device-screenshot/...`, but the shared Blob contract does not define `device-screenshot` as a namespace. Runtime-generated CLI artifacts should use `blob://runtime-artifact/...`.

## Proposed Solution

Patch contract-relevant tests to use `runtime-artifact` for screenshot artifacts. Leave unrelated low-level storage tests alone unless they represent CLI/tool-output contract examples.

## Acceptance Criteria

- No `device-screenshot` namespace remains in tool-output/CLI contract tests.
- Screenshot artifact examples use `blob://runtime-artifact/...`.
- Projection/runtime tests still pass.

## Verification Plan

- Run `rg device-screenshot` after patching.
- Run affected Cortex and agent-runtime tests.

## Risks

- Over-broad replacement could alter unrelated behavior; keep patch scoped to contract tests.

## Assumptions

- `runtime-artifact` is the intended namespace for device screenshot artifacts emitted by CLI tools.
