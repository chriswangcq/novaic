# Filter Focused Pytest Target Inventory Ticket

## Problem Definition

The P513 selected focused pytest target list includes a non-test `__init__.py` file. The list and inventory count must be corrected before focused test execution uses it.

## Proposed Solution

Regenerate `selected-focused-test-files.txt` from the filename candidates using a `test_*.py` filter, update the inventory artifact/counts, and save a guard artifact proving no non-test path remains.

## Acceptance Criteria

- Selected focused target list contains only paths ending in `/test_*.py`.
- Inventory count is updated.
- Evidence artifact records zero non-test selected paths.

## Verification Plan

- Run a negative grep against the selected list for paths that do not match `/test_*.py`.
- Record the updated count and artifact paths.

## Risks

- Filtering could accidentally remove legitimate test files if their naming differs from `test_*.py`.

## Assumptions

- Pytest targets in this repository use the `test_*.py` convention.
