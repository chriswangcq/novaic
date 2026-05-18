# Child Problem: media/base64 tool output contract

## Problem

Device/display/media tool output must not leak large base64 payloads into shell text or LLM context. It should use concise terminal text plus blob/artifact manifests.

## Success Criteria

- Device screenshot/media CLI returns blob/artifact manifest rather than raw base64 text.
- Display/image projection does not serialize base64 as text in LLM messages.
- Focused tests or scans prove the contract.
