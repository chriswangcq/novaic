# Ticket: isolate backend activity projection legacy labels

## Problem Definition

Backend activity projection keeps labels for archived records that used old direct tools. The map is useful, but raw old tool names should be centralized and marked as archived compatibility.

## Proposed Solution

- Introduce archived-compatibility constants in `activity_projection.py`.
- Move old direct-tool labels into an explicitly named legacy map.
- Keep shell `desc` and command projection as the primary current path.

## Acceptance Criteria

- Legacy labels are clearly named archived compatibility.
- Current shell behavior is unchanged.
- Focused runtime activity projection tests pass.

## Verification Plan

- Focused grep over `activity_projection.py`.
- Run `test_pr193_activity_projection.py`.

## Risk

Do not remove rendering for old archived monitor records.
