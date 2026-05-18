# Convert Gemini user list content into native parts

## Problem Definition

`GoogleProvider._convert_messages` currently stringifies non-string user content. This breaks display-perception image prompts and risks putting data URLs into text.

## Proposed Solution

Add a Google-specific content converter that maps OpenAI-style content arrays to Gemini `parts`: text parts for text/string items, inline image parts for data URL `image_url`, placeholder text for non-data image URLs, and diagnostic text for unsupported blocks.

## Acceptance Criteria

- Data URL images become `inlineData` parts with `mimeType` and base64 `data`.
- Text remains text.
- Image base64 does not appear in text parts.
- Existing tool/function conversion behavior remains unchanged.

## Verification Plan

Run a small provider conversion smoke check in this ticket; full tests are in the sibling test ticket.

## Risks

- Gemini JSON field casing must match current provider request conventions.

## Assumptions

- The existing provider uses camelCase request fields such as `functionCall`, so image parts should use `inlineData` and `mimeType`.
