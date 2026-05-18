# Active-stack-after-display media preservation

## Problem

Audit runtime context assembly after step-ref expansion so a `[Active skill stack]` system message following a display tool result does not strip, downgrade, or hide the current display media before the next LLM request.

## Success Criteria

- Map the context/multimodal helper that extracts display perception media into provider-visible content.
- Prove display media survives when a system active-stack message follows the display tool result.
- Prove the original display tool message remains placeholder-only after media extraction.
- Add or verify focused regression coverage for this exact ordering.
