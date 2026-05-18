# Runtime LLM Request Projection Path Inventory

## Problem

Audit agent-runtime LLM request/context assembly paths to verify tool outputs, display perception, artifacts, and active stack messages are projected into LLM requests through the intended contract. This belongs under P564 because the recent regression appeared inside the LLM request body, where display/tool output was still visible as raw or misplaced content.

## Success Criteria

- Records exact scan commands and outputs for runtime request assembly, message conversion, tool-result projection, multimodal/image handling, and active stack injection.
- Reads relevant runtime code/test slices with line references.
- Classifies each hit bucket as intended, risky, removable, or follow-up.
- Separates valid current-turn image/perception content from invalid historical tool text or base64 embedding.
- Captures any high-confidence risky residue for P554 remediation.

