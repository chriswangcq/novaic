# Ticket: fix display and LLM image projection contract

## Problem Definition

The display/image path must not serialize image bytes as text in LLM messages, but it also must actually provide the image to the model when the agent calls `display` on a blob artifact. Previous observed failures showed both bad modes: base64 appearing as text history and later image artifacts not being available to model perception.

## Proposed Solution

- Trace display tool handling from blob input through runtime tool result, context/history projection, and LLM Factory request assembly.
- Identify where image artifacts are converted into public tool text, image blocks, or history payloads.
- Patch active code so display tool observations remain concise while the subsequent LLM request receives provider-compatible image content.
- Remove or isolate legacy text-base64 projection paths if they are still active.
- Add focused tests that inspect assembled request messages and prove displayed image content is not emitted as text base64.

## Acceptance Criteria

- `display` tool result text is concise and contains no raw base64 or data URL text blob.
- The next LLM request after `display(blob://...)` includes an image in a model-compatible non-text representation.
- Existing/historical display text fixtures are explicitly classified or updated.
- Focused tests fail if display image data is serialized as `role=tool` text base64.

## Verification Plan

- Run `rg` scans for display projection, `data:image`, image block creation, and base64 handling in runtime and Cortex.
- Run or add unit tests for display tool result handling and LLM message assembly.
- Inspect request-shape fixtures/tests rather than relying on UI monitor presentation alone.

## Risks

- Different model providers may require different image block shapes; tests should assert the internal contract before provider adaptation where possible.
- Eliminating all inline base64 is not always possible inside provider-native image payloads, but it must not be represented as plain text message content.

## Assumptions

- Blob references are the durable image source.
- The desired model-visible image path can use native multimodal content or a compact internal artifact reference that the provider adapter resolves.
