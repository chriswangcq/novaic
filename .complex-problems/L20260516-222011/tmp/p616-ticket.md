# Inventory Shell Output Contract Tests and Guardrails

## Problem Definition

P616 must map tests guarding the shell output contract: bounded terminal text, artifact manifests, no raw base64 history leakage, monitor summaries, and full-output recovery via payload references.

## Proposed Solution

Scan test suites for shell output, tool-output, artifact, base64, payload_ref, monitor preview, and context history tests. Cite exact test slices, classify invariant coverage, and run the focused test set. Create a follow-up if any key invariant lacks coverage.

## Acceptance Criteria

- Exact test scan and cited slices are recorded.
- Each key shell output invariant is mapped to one or more tests.
- Focused guardrail test set passes.
- Missing coverage is forwarded as a follow-up if found.

## Verification Plan

Run the shell wrapper tests from P614 plus Cortex persistence tests from P615 and monitor/backend preview tests from P603/P604 as appropriate.

## Risks

- There may be duplicate tests with old PR names; classify coverage by invariant, not by test filename.

## Assumptions

- Existing tests can serve as guardrails if they explicitly assert the contract.
