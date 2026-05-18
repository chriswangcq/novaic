# Verify step index metadata and corrupt-index behavior

## Problem Definition

`steps/_index.jsonl` is the compact browsing surface for tool history. It must include stable refs and enough metadata to avoid opening heavy step files, and it must not silently hide corrupted index lines because that masks history integrity issues.

## Proposed Solution

Audit `write_step` index construction and `read_step_index`. Verify tests cover `step_ref`, `payload_ref`, tool/status/duration, and artifact markers. If corrupt index lines are silently ignored, replace that with explicit failure behavior and add a targeted regression test.

## Acceptance Criteria

- `write_step` index construction and `read_step_index` are mapped with source pointers.
- Index entries include `step_ref`, `payload_ref`, tool/status/duration metadata when present.
- Artifact-bearing observations or steps get a compact `has_artifacts` marker.
- Corrupt `_index.jsonl` lines are not silently swallowed unless there is an explicit documented reason and test.

## Verification Plan

Run `test_step_index_outcome.py` after any patch. Add tests for corrupt index behavior if missing, and keep the API contract deterministic.

## Risks

- Tightening corrupt-index behavior may expose existing bad archived data during reads.
- Artifact markers may only consider top-level `artifacts`; observation-level artifact manifests may need a later sibling if active tools use that shape.

## Assumptions

- Active new writes should fail loudly on corrupt index data rather than hiding missing history.
- Historical data cleanup is acceptable if older corrupted index rows exist.
