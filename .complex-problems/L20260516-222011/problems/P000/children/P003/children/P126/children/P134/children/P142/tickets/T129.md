# Audit workspace tool step normalization and index contract

## Problem Definition

`P142` asks whether Cortex workspace step materialization keeps tool results pointer-oriented and indexable. The risky paths are `normalize_step`, `write_step`, and `write_step_projection`: if any of them accept inline raw output, lose `payload_ref`, or under-index artifact-bearing steps, later context assembly can leak large payloads or make complete reconstruction impossible.

## Proposed Solution

Perform a focused source-and-test audit of the workspace step pipeline. Map the implementation with line-level pointers, run the relevant regression tests, and patch any discovered gap in normalization, payload externalization, or `_index.jsonl` metadata. Treat this as a split if inspection shows more than one behavioral gap or if the fix crosses both Cortex workspace code and runtime projection code.

## Acceptance Criteria

- Source pointers identify `normalize_step`, `write_step`, and `write_step_projection`.
- The audit proves tool step writes reject inline `result` and require an observation percept.
- The audit proves raw payload data is externalized through `write_payload`, with `payload_ref` mirrored into the stored observation.
- The audit proves step index rows preserve `step_ref`, `payload_ref`, duration, tool/status metadata, and an artifact marker when artifacts exist.
- Any code gap found during inspection is fixed with targeted tests before recording success.

## Verification Plan

Run focused Cortex tests for step indexing and payload inspection first, then add or update tests if the source audit finds uncovered behavior. Use `rg`, `nl`, and `jq` to inspect only the relevant source and stored contract surfaces rather than loading bulk payload data.

## Risks

- A test may cover the happy path while `write_step_projection` still allows legacy inline result shapes.
- Index metadata could look complete but fail to distinguish artifact-bearing steps.
- A normalization change may affect archived step readability, so the check must separate active contract requirements from historical compatibility.

## Assumptions

- Historical archived step files may remain readable, but new writes do not need backward-compatible inline payload behavior.
- The authoritative contract is pointer-oriented storage plus compact materialized indexes; full raw payloads belong in payload storage, not step JSON or LLM context.
