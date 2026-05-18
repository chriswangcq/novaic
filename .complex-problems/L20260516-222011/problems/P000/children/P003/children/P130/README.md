# Provider-native media adapter boundary audit

## Problem

Some image bytes may legitimately appear at the final provider API boundary as `image_url` or equivalent multimodal content. That transformation must be isolated from Cortex history and must not be confused with text-context leakage.

## Success Criteria

- Provider-native image construction code is mapped and separated from Cortex history projection.
- Blob/display image data is only converted to provider-native media at the final model-call boundary.
- Provider request tests or fixtures prove image content is sent in the expected multimodal format, not as plain text tool history.
- Any stale comments/tests implying base64 text history is acceptable are corrected or classified as provider-boundary-only.
- The design distinction between “history projection” and “provider media payload” is documented in code comments or tests where ambiguity existed.
