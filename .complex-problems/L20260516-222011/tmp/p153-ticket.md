# Classify context.jsonl helper callers

## Problem Definition

Every active caller of `context.jsonl` helpers must be classified, otherwise materialized projection code can quietly become a second context authority or stale compatibility path.

## Proposed Solution

Scan for `read_context`, `append_context`, `append_context_projection`, `append_context_batch`, and `append_context_batch_projection` calls in non-test code. Classify each as debug/read API, projection write, compatibility, stale, or unsafe. Patch unsafe/stale callers or record a tightly scoped gap.

## Acceptance Criteria

- All non-test caller sites are listed with source pointers.
- Each caller has a precise role classification.
- No unsafe/stale caller remains unaddressed.

## Verification Plan

Use `rg` and line-numbered source reads. Run context API tests if caller behavior is touched.

## Risks

- Public `context_read` may be a user/debug API and not LLM authority; classification must not overreach.

## Assumptions

- LLM prepare authority is handled in sibling `P154`.
