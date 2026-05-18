# Provider-Native Image Projection Audit

## Problem

Sanitized display history must not break current-turn image perception. The current display result should reach provider adapters as native image content only through the dedicated multimodal handoff path.

## Success Criteria

- Inspect runtime multimodal extraction/provider message conversion.
- Verify current display perception becomes provider-native image content where supported.
- Verify ordinary tool text/history remains sanitized.
- Fix any boundary where image bytes are put into text instead of provider-native content.
