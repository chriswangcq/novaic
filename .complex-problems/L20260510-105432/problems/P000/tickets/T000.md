# Promote stable sandbox primitives into common base modules

## Problem Definition

Some shell execution pieces are generic infrastructure but currently live under `novaic-cortex`. That blurs business boundaries and makes reusable, stable logic look Cortex-specific.

## Proposed Solution

Audit and split the work into:

- Generic process execution substrate.
- Generic mount namespace/bind mount substrate.
- Generic filesystem snapshot/diff/path helpers.
- Cortex migration to consume these base modules while retaining Cortex-specific LogicalFS/Workspace/shell capability semantics in Cortex.

## Acceptance Criteria

- Base infrastructure modules live under `novaic-common/common/sandbox`.
- Cortex-specific semantics remain in `novaic-cortex`.
- No duplicate implementations remain in Cortex for the extracted primitives.
- Tests cover base modules and Cortex integration.

## Verification Plan

- Run `novaic-common` tests for new base modules.
- Run `novaic-cortex` full tests.
- Run residue scans for duplicate old implementation names.

## Risks

- Over-extraction could leak Cortex concepts into common or create abstractions too early.
- Under-extraction would leave the codebase still ambiguous.

## Assumptions

- This is a shared library/base module extraction, not a new network service.
