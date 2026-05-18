# Check: P435 Cortex CLI and shell capability cleanup

## Verdict

Success for the CLI/shell capability boundary.

## Evidence Reviewed

- Result `R417`
- Focused tests: `28 passed`
- CLI/capability inventory and source slices for `devicectl`, `agentctl media`, and `cortex payload`.

## Criteria Map

- Device image/file outputs avoid raw base64 shell stdout: satisfied by wrapper code and tests asserting no raw base64 / `"screenshot":` / `"data":` leaks in stdout.
- Large/binary outputs use blob-backed artifact manifests: satisfied for HD screenshot and file-pull via `_put_blob()` and `tool-output.v1.artifacts`.
- Payload inspection is explicit and bounded: satisfied by `cortex payload read/search/summarize/qa` tests and help text.
- Provider-boundary media base64 is not confused with shell stdout: satisfied; `agentctl media audio-qa` base64-encodes audio only inside the Factory API request after fetching `blob://` input.
- Runtime bridge and context projection use are not overclaimed: satisfied; P436 remains open for that boundary.

## Execution Map

The check treats CLI/shell capability cleanup as a terminal-output contract, not as the full LLM context assembly contract. It confirms the shell-facing surfaces are clean while keeping the runtime bridge question separate.

## Stress Test

I looked for the same failure class that previously hurt screenshots: raw base64 or raw device response fields leaking through shell stdout. Focused tests explicitly cover screenshot and file-pull outputs, and source inspection confirms the only base64 use in device handling is decoded before blob upload.

## Residual Risk

None inside P435's CLI/shell capability scope. P436 must still decide whether runtime bridge use of materialized context projection endpoints is acceptable or stale.
