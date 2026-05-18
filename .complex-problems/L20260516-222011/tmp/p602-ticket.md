# Audit UI Display Artifact and BlobRef Rendering Boundary

## Problem Definition

P602 must verify UI handling of display artifacts and BlobRefs across chat/application/frontend surfaces, ensuring images are rendered through BlobRef/artifact/display paths instead of raw base64 tool text.

## Proposed Solution

Reuse evidence from P608 where applicable, then run a focused UI scan for BlobRef, artifact, display, image, thumbnail, data URL, and base64 rendering paths. Cite the exact UI slices and tests that demonstrate BlobRef/artifact rendering behavior and classify any base64 usage as safe debug/provider code or risky residue.

## Acceptance Criteria

- Exact UI scans are recorded for BlobRef, artifact, image, thumbnail, display, data URL, and base64 paths.
- Relevant frontend slices are cited for BlobRef/artifact rendering behavior.
- Any base64 rendering found is classified as safe/non-UI, debug/provider request, or a follow-up-worthy UI risk.
- A follow-up is created if UI display requires raw base64 from tool text.

## Verification Plan

Run focused frontend tests around attachment conversion/rendering and ActivityTimeline redaction. If scans reveal additional relevant UI tests, include them. Record evidence and test outputs as ledger artifacts.

## Risks

- This overlaps P608, so the result must distinguish broad UI display surfaces from Agent Monitor-specific artifact rendering.
- Search terms may find safe base64 constants unrelated to image display; classify carefully instead of deleting blindly.

## Assumptions

- Product goal is not to implement new thumbnail UI here; correctness means no raw base64 tool text requirement in normal UI display paths.
