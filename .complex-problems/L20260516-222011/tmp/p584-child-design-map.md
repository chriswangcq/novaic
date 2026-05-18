# Child Problem: Display BlobRef perception design and call-path map

## Problem

Before editing, identify the exact path from display executor result to Cortex step payload, step-result formatting, runtime step expansion, multimodal processing, and provider request construction. Choose the smallest clean boundary where BlobRef media can be resolved without storing base64 in durable payload.

## Success Criteria

- Records call-path slices with line references.
- Identifies the authoritative owner for Blob fetch at perception time.
- Produces an implementation plan that preserves current display image delivery and history text-only behavior.

