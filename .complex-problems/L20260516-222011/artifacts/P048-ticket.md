# Ticket: enforce media and base64 output contract

## Problem Definition

Media-producing tools, especially screenshot/display flows, must not push large base64 payloads into terminal text, Cortex step text, or LLM request messages. The desired contract is terminal-style concise text plus blob/artifact manifests, with actual media loaded through the image/display projection path.

## Proposed Solution

- Audit current media and device CLI output paths for raw base64, inline image data, data URLs, or overlarge JSON text.
- Audit display/image projection and LLM context assembly to ensure image bytes are represented as model-native image inputs or compact artifact references, not text content.
- Patch any active path that still serializes image/base64 payloads into text.
- Add or update focused tests/scans proving:
  - device screenshot CLI emits a blob/artifact manifest,
  - shell observations remain concise terminal text,
  - display/image projection does not convert media bytes into text messages.

## Acceptance Criteria

- No active screenshot/media CLI returns raw base64 in stdout.
- LLM request assembly for display/image inputs uses non-text image content or compact references according to the provider contract.
- Shell-visible media output remains concise and points to blob/artifact URIs.
- Tests or scans fail if base64-like image payloads appear in shell/display text paths.

## Verification Plan

- Run focused `rg` scans for `base64`, `data:image`, screenshot payload fields, and display content construction.
- Run targeted tests around device CLI contracts, display tool projection, and LLM message assembly.
- If code is changed, run the smallest relevant test set plus any existing contract guard tests.

## Risks

- Some tests may intentionally include tiny base64 fixtures; these should be renamed/classified if retained.
- Provider APIs may require different multimodal payload shapes; verification must inspect the actual request assembly layer rather than assuming the UI/monitor projection is equivalent.
- Blob/artifact manifests must remain user- and agent-readable enough for follow-up shell inspection.

## Assumptions

- Blob storage is the intended durable carrier for screenshots and media artifacts.
- Shell should behave like a human terminal: concise text, bounded output, and pointers to files/artifacts rather than opaque binary payloads.
