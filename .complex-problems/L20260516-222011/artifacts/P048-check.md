# Media/Base64 Tool Output Contract Check

## Summary

Successful. The media/base64 contract is now covered across CLI stdout, shell/public tool output, Cortex history/projection, display perception, provider adaptation, and log redaction.

## Evidence

- `R051` summarizes four closed child branches: CLI media, display/LLM projection, shell terminal semantics, and base64 guards.
- Code changes hardened runtime display public output and generic unstructured media fallback.
- Tests were added/strengthened for `/9j/` shell stdout, shell raw payload projection, non-display `_mcp_content` fallback, provider conversion, and redaction.

## Criteria Map

- No active screenshot/media CLI returns raw base64 in stdout:
  - Satisfied by P050 CLI manifest tests.
- LLM request assembly for display/image inputs uses non-text image content or compact references:
  - Satisfied by P051 runtime/Cortex/provider tests.
- Shell-visible media output remains concise and points to blob/artifact URIs:
  - Satisfied by P050 and P052.
- Tests/scans fail if base64-like image payloads appear in shell/display text paths:
  - Satisfied by P052/P053 regression tests and guard hardening.

## Execution Map

- `P050`: CLI manifest contract.
- `P051`: display-to-LLM image contract.
- `P052`: shell terminal-shaped contract.
- `P053`: broad regression guard.

## Stress Test

- The check includes the two concrete failure classes observed by the user:
  - screenshot base64 (`/9j/...`) appears as tool text,
  - display result injects image base64 into `role=tool` text instead of model image content.

## Residual Risk

- Low. Structured provider image payloads and explicit display perception still legitimately carry base64 as image data. That is not a leak under the contract.

## Result IDs

- R051
