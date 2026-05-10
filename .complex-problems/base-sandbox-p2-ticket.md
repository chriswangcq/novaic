# Build common sandbox modules

## Problem Definition

Common base infrastructure modules for process execution, mount namespace, and filesystem helpers do not exist yet.

## Proposed Solution

Create `common/sandbox` package with `process.py`, `mount_namespace.py`, and `filesystem.py`, plus tests in `novaic-common/tests`.

## Acceptance Criteria

- Common package exports stable APIs.
- Tests cover process success/timeout, bind mount command construction, availability detection shape, file stats/diff, cwd resolution, path sanitization, and safe component normalization.
- No Cortex imports appear in common modules.

## Verification Plan

- Run targeted `novaic-common` tests.
- Compile common modules.

## Risks

- Tests for actual `unshare` should not require root; command construction and availability detection are enough at the common layer.

## Assumptions

- Execution integration remains tested in Cortex.
