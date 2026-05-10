# Migrate Cortex sandbox code to common primitives

## Problem Definition

Cortex still owns local copies of generic process, mount namespace, and filesystem helpers.

## Proposed Solution

Update `novaic-cortex` to import common sandbox primitives, remove the local `sandbox_exec.py` implementation, and keep only Cortex-specific LogicalFS and facade logic.

## Acceptance Criteria

- `sandbox.py` imports process primitives from `common.sandbox.process`.
- `logical_fs.py` imports mount/filesystem primitives from `common.sandbox`.
- `novaic_cortex/sandbox_exec.py` is deleted.
- Cortex tests pass.

## Verification Plan

- Compile Cortex modules with `PYTHONPATH=../novaic-common:.`.
- Run full `novaic-cortex` tests.
- Scan for local duplicate implementations.

## Risks

- Tests that patch private helper locations may need to target the new canonical module.

## Assumptions

- `novaic-common` is available on Cortex PYTHONPATH in dev/runtime, as existing Cortex imports already use `common.*`.
