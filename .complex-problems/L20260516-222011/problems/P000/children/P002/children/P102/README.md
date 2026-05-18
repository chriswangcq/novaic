# Shell Output and Desc Contract Audit

## Problem

Shell execution should expose bounded terminal text, preserve useful monitor `desc`, and avoid raw binary/base64 payloads in LLM-visible tool results.

## Success Criteria

- Inspect shell output contract implementation and tests.
- Verify `desc` is accepted and surfaced safely.
- Verify truncation/bounded terminal text behavior.
- Fix or route any gap found.
