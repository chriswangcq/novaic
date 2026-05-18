# Ticket: Audit And Remove Or Narrow SmartValue

## Problem Definition

`novaic-app/src/components/Visual/SmartValue.tsx` contains generic raw value rendering behavior, including `JSON.stringify` fallback. If unused, it should be deleted to avoid dormant raw-renderer residue; if used, it must be narrowed.

## Proposed Solution

- Audit all imports/usages of `SmartValue`.
- If unused, physically delete `SmartValue.tsx`.
- If used, replace or narrow its raw JSON fallback so large/base64-like values cannot be dumped.
- Adjust imports/tests if needed.

## Acceptance Criteria

- Usage audit is recorded with exact search evidence.
- `SmartValue.tsx` is deleted if unused.
- If not deleted, its raw rendering behavior is safely narrowed and tested.
- Focused TypeScript/test checks for touched app files pass or unrelated pre-existing failures are documented.

## Verification Plan

- Run `rg -n "SmartValue" novaic-app/src`.
- If deleting, run focused import/TypeScript scans after deletion.
- Run relevant frontend test or `npm`/`pnpm` check available in `novaic-app`.
- Run `git diff --check` for touched app files.
