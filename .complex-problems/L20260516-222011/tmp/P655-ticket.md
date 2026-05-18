# Audit Blob Workspace Boundary Tests and Guardrails

## Problem Definition

The project needs executable guardrails proving Blob remains byte/artifact storage while live RO/RW semantics go through Workspace/LogicalFS. Existing tests may be incomplete or too imprecise.

## Proposed Solution

Review current boundary tests/CI scans, ensure they cover direct object authority and BlobRef projection correctly, update tests or CI if needed, and run the focused test suite.

## Acceptance Criteria

- Identifies current guardrail tests and what they protect.
- Fixes overly broad or missing guardrails discovered during audit.
- Runs focused guardrail tests.
- Records any remaining gap as a child/follow-up rather than claiming closure.

## Verification Plan

Inspect `test_blob_boundary_guard.py`, `blob_boundary_policy.py`, related workspace registry dependency tests, and CI references. Run the focused tests after any changes.

## Risks

- A guardrail can be too broad and block valid BlobRef projection.
- A guardrail can be too narrow and miss direct `/v1/objects` workspace bypasses.

## Assumptions

- The guardrail should distinguish Blob object authority, BlobRef byte access, and BlobRef manifest/projection usage.
