# Inventory Legacy Base64 and Multimodal Compatibility Residue

## Problem Definition

P577 must find stale base64/data URI/image_url/multimodal/provider compatibility paths that could bypass the current BlobRef/display/shell contract and reintroduce raw media text into history or logs.

## Proposed Solution

Split the inventory into provider-adapter/request formatting, runtime/Cortex/display compatibility paths, and UI/test residue classification. Each child records exact scans, classifies hits, and creates follow-up for reachable risky residue.

## Acceptance Criteria

- Broad scans for base64/data URI/image_url/multimodal/provider terms are recorded.
- Relevant hits are classified by layer and reachability.
- Any active old compatibility path that bypasses the artifact/display contract is removed or followed up.
- Intended provider API image formatting is preserved and documented as boundary behavior.

## Verification Plan

Run focused provider log/redaction tests, runtime projection tests, and frontend guard tests as needed per child.

## Risks

- Provider request formatting legitimately contains image bytes after the explicit display-perception boundary; do not delete that.
- Search results include many tests that intentionally assert redaction/absence.

## Assumptions

- Backward compatibility for old raw base64 tool outputs is not required unless it is strictly provider-boundary formatting.
