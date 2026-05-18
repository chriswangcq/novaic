# App raw JSON and truncation primitives discovery ticket

## Problem Definition

Shared UI primitives for raw JSON, smart values, truncation, copy/detail rendering, and media detection may still render raw tool/media payloads or `_mcp_content` envelopes in user-visible views.

## Proposed Solution

Discover shared UI primitives in `novaic-app/src` that render JSON, arbitrary values, previews, images, blobs, raw strings, or truncated details. Inspect high-signal source and tests, classify whether each path is user-facing and whether it sanitizes raw payload-like content.

## Acceptance Criteria

- Shared JSON/value/truncation/sanitization primitive files are discovered.
- Suspicious raw JSON, pretty-print, copy/detail, `_mcp_content`, base64/data URL, BlobRef, artifact, and truncation hits are classified.
- Remediation candidates are listed if shared primitives can leak raw payloads.
- No shared UI primitive files are modified.

## Verification Plan

Use bounded `rg --files`, focused `rg -n -i`, targeted file slices, and relevant tests if available.

## Risks

- Some primitives are intentionally developer/debug oriented; classify normal user-facing usage separately from internal debug usage.
- BlobRef image previews can legitimately render images by fetching bytes, which should not be misclassified as raw payload leakage.

## Assumptions

- Shared UI primitives live under `novaic-app/src/components/Visual`, `novaic-app/src/components/Common`, and related hooks/types.
