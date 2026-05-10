# Encode Blob Boundary Guardrail Policy

## Problem Definition

The guardrail needs a precise policy before scanning source. The repo contains legitimate Blob byte flows and transitional persistence internals, so the boundary cannot be expressed as a single forbidden string.

## Proposed Solution

Create a small test-support policy module that names the allowed source locations, forbidden live-file bypass patterns, and positive/negative fixture snippets. The implementation ticket will import this module instead of duplicating boundary rules in ad hoc test code.

## Acceptance Criteria

- The policy explicitly allows Blob byte flows for payload, display, audio, attachment, artifact, and tests.
- The policy explicitly names transitional persistence internals and the single live-file authority boundary.
- The policy explicitly marks Workspace/API/runtime/sandbox code as forbidden locations for direct Blob object-store authority.
- The policy includes synthetic allowed and forbidden snippets for later guardrail proof.

## Verification Plan

- Add the policy file.
- Run a syntax/import check for the policy file.
- Confirm the policy references match P006 findings.

## Risks

- A policy that is too broad will permit future bypasses.
- A policy that is too narrow will block legitimate Blob byte use.

## Assumptions

- The policy is test/support infrastructure, not production runtime behavior.
