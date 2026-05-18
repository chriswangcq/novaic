# P617 Provider Adapter Multimodal Boundary Classification

## Intended Provider Boundary

Provider request payloads may contain provider-native image content after the explicit display-perception boundary. This is not shell/history text and must remain available for multimodal model calls.

## Redacted Log Boundary

Factory log snapshots redact OpenAI `image_url` data URLs and Anthropic `source.data` image content. This prevents large/raw media from being exposed as log/debug JSON while preserving call metadata.

## Risky Residue

No risky active provider/factory compatibility path found that stores or displays raw image bytes unexpectedly outside the intended provider request boundary.
