# Child Problem: Display tool implementation and blob/artifact contract

## Problem

Audit the display tool implementation and configuration to verify image/media artifacts are loaded from BlobRefs or equivalent stable artifact references, and that display's direct tool result is a concise acknowledgement rather than raw image/base64 text.

## Success Criteria

- Records scan commands for display tool definitions and handlers.
- Reads display implementation/configuration slices with line references.
- Classifies display return payloads as intended perception, bounded text, risky raw media, or follow-up.
- Forwards any raw base64/history residue to P554.
