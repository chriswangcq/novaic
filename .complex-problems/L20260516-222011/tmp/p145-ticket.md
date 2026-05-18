# Verify normalize_step rejects unsafe legacy step shapes

## Problem Definition

`normalize_step` must be the workspace boundary that accepts only structured tool observations for new step writes. If it still accepts inline raw `result` fields or missing observations, later payload and context guarantees become advisory rather than enforced.

## Proposed Solution

Inspect `novaic_cortex.workspace.normalize_step`, identify its validation behavior, run the focused step-index tests, and add a regression test or patch if inline `result` or missing observation is still accepted on the active write path.

## Acceptance Criteria

- `normalize_step` source behavior is mapped with line references.
- Inline `result` input is proven rejected for new normalized step data.
- Missing/invalid observation input is proven rejected.
- Any compatibility behavior is clearly shown as outside active new-write usage.

## Verification Plan

Use `nl`/`rg` to inspect the implementation, then run the focused `test_step_index_outcome.py` tests. If coverage is missing, add a targeted test in that file and rerun it.

## Risks

- A lower-level helper may be strict, but API call sites could bypass it; that remains for the later projection call-site child.
- Existing archived data may contain legacy shape; the fix must not claim archived files are rewritten.

## Assumptions

- New workspace step writes should use `observation` as the canonical result container.
- Historical read compatibility can exist only if it does not weaken new write validation.
