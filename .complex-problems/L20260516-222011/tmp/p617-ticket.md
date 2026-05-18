# Audit Provider Adapter Multimodal Boundary Residue

## Problem Definition

P617 must classify provider/factory multimodal branches involving base64/data URI/image_url so intended provider request formatting is not confused with stale raw-history/log residue.

## Proposed Solution

Scan `novaic-llm-factory` provider routes/contracts/static logs for base64/data URI/image_url/multimodal terms, cite relevant slices, classify each relevant branch, and run focused chat/log redaction tests.

## Acceptance Criteria

- Exact provider/factory scan is recorded.
- Provider request formatting vs log/redaction behavior is classified with pointers.
- Focused factory tests pass.
- Risky raw media persistence/logging residue is followed up if found.

## Verification Plan

Run `test_log_routes.py` and chat route redaction tests for OpenAI/Anthropic image payloads.

## Risks

- Provider-native multimodal request formatting legitimately contains image data after the explicit perception boundary; do not delete intended provider call payloads.

## Assumptions

- Factory log snapshots should redact image payload data even if the provider request carries it.
