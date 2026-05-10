# Verify refactor and scan for misleading residue

## Problem Definition

After module extraction and dependency cleanup, we need evidence that the new layering is active and old fallback/duplicate logic did not survive.

## Proposed Solution

Run compile/import checks, targeted tests, and grep-style residue scans. If gaps appear, fix them or record a follow-up.

## Acceptance Criteria

- New modules compile/import.
- Targeted tests pass or environment skips are explicitly explained.
- `sandbox.py` is only facade/orchestrator plus policy rejection.
- No local fallback/path adapter logic remains in the active shell path.
- Ledger result/check accurately report remaining risk.

## Verification Plan

- `python -m py_compile` on changed Cortex modules.
- `pytest` targeted sandbox/workspace/capability/projection tests.
- `rg` scan for old fallback/rewrite helpers and duplicate class definitions.

## Risks

- Local environment cannot execute mount namespace shell tests; remote smoke may be needed separately if deployment verification is requested.

## Assumptions

- Do not deploy unless verification reveals a runtime need or the user asks; this task is architectural cleanup.
