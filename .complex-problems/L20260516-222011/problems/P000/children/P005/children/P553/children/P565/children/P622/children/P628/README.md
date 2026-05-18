# Sandbox Wire Base64 Public-History Residue

## Problem

Classify base64/stdout_b64/stderr_b64 handling across SDK/service/Cortex/shell projection to confirm bytes stay in private wire or durable payloads and do not leak into LLM history/tool text.

## Success Criteria

- Records exact scans for base64/stdout_b64/stderr_b64/data URL/image payload terms.
- Cites SDK/service/Cortex/runtime projection slices.
- Classifies private wire encoding vs public history leakage.
- Runs focused shell/artifact projection tests.
- Creates follow-up if public LLM history can receive raw base64 bytes.
