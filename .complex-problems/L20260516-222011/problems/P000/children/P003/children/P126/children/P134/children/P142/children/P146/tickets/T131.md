# Verify write_step payload_ref mirroring and external payload storage

## Problem Definition

`write_step` must keep full payload data outside the step file while preserving an accurate `payload_ref` in both the stored step and the observation. The contract is fragile when local payload refs are replaced by blob refs, because stale refs can make step history unrecoverable.

## Proposed Solution

Audit `normalize_step`/`write_step` payload handling and focused tests for local payloads and blob-backed external payloads. Patch tests or implementation if the actual persisted step does not mirror the final payload ref into the observation.

## Acceptance Criteria

- Source pointers identify where payload data is removed from the step and stored through payload storage.
- Local payload writes preserve a readable `payload_ref` in the step and observation.
- Large/blob-backed payload writes replace stale source refs with the actual blob-backed `payload_ref`.
- Focused tests verify both local and external payload readback.

## Verification Plan

Inspect `workspace.py` around payload handling and run `test_step_index_outcome.py` plus `test_payload_inspection_api.py`. Add a regression test if observation mirroring is only partially covered.

## Risks

- Tests may assert top-level `payload_ref` but not observation-level mirroring.
- Blob-backed tests may use a fake client that hides metadata or manifest mistakes.

## Assumptions

- Raw payload bytes/text should never remain inside `steps/*.json`.
- `payload_ref` in the stored observation should match the actual persisted payload reference, not merely the caller's original source ref.
