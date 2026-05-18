# Business/subscriber candidate disposition ticket

## Problem Definition

P715 found possible Business/subscriber boundary residue in docs and code scans. Before patching, each candidate needs a concrete disposition so active stale claims are not mixed with historical comparison text, test fixtures, or already-clean paths.

## Proposed Solution

Review P715 scan artifacts and the most relevant source/doc files. Produce a candidate table with disposition, evidence pointer, and recommended next action. Pay special attention to `docs/entangled-architecture.md` entity CRUD/Gateway/Business wording, subscriber aggregation config, and any text implying Business/subscriber owns Queue/Runtime/Cortex session lifecycle.

## Acceptance Criteria

- Cleanup candidates from P715 are enumerated with evidence pointers.
- Each candidate has a disposition: patch, retain as current, retain as historical comparison, test-only, already clean, or follow-up candidate.
- The result identifies exact files/lines or scan artifact pointers for downstream remediation.
- No source/docs are patched in this ticket.

## Verification Plan

Use `rg`, `sed`, and P715 scan artifacts to sample and validate candidates. Cross-check active architecture docs when classifying ambiguous Business/Gateway/Entangled claims.

## Risks

- Over-classifying from search hits without reading surrounding context could delete useful historical comparison text.
- Under-classifying could leave vague remediation instructions for P718/P719.

## Assumptions

- P715 scan artifacts are available and current enough for this remediation pass.
- The exact patching work belongs to later child problems, not this disposition ticket.
