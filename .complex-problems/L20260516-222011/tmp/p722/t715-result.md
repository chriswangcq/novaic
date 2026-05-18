# Artifact/display/context projection discovery

## Summary

The screenshot/artifact pipeline is now understood end to end. Shell outputs are bounded terminal text plus `tool-output.v1` Blob manifests. History replay is manifest-only and does not re-inject raw media bytes. `display` is the explicit current-round perception path: it fetches Blob bytes, stores only public placeholder/history metadata, resolves image refs only for current display perception, and passes provider-native structured image content to Factory. Remaining cleanup is legacy/standalone surface reduction, not an active shell/display/context leak.

## Child Results Used

- `P725` / `R708`: shell artifact manifest output contract discovery.
- `P726` / `R712`: Blob artifact manifest and history replay discovery.
- `P727` / `R713`: display current-round LLM image projection discovery.
- `P728` / `R724`: legacy/standalone media-byte surface classification.

## End-to-End Flow

1. Shell command such as `devicectl hd screenshot` calls Device/HD.
2. Cortex shell wrapper decodes raw device screenshot bytes internally.
3. Cortex uploads image bytes to Blob as `blob://runtime-artifact/...`.
4. Shell stdout receives bounded terminal text containing a `tool-output.v1` manifest and artifact metadata, not raw base64.
5. Runtime stores bounded public tool output and durable payload pointers.
6. Later context/history replay projects manifest-only text and does not expand old images into text/base64.
7. If the agent explicitly calls `display` on a Blob URI in the current round, Runtime fetches Blob bytes and stores an `image_ref` in durable payload.
8. The next LLM request resolves only current display perception into provider-native image content.

## Current Good Contracts

- Shell: terminal text + Blob artifact manifests.
- History: bounded text/manifest-only; raw stdout/media retained only as durable payload diagnostics where applicable.
- Display: current-round visual perception only; public history redacts inline image data.
- Factory request: structured multimodal message content is preserved for provider API transport.

## Cleanup Candidates

1. Retire or convert `novaic-device/device/vmcontrol_routes.py` screenshot route, which still returns inline MCP image content.
2. Remove unused `base64` import in `novaic-mcp-vmuse/src/novaic_mcp_vmuse/tools/windows.py`.
3. Update or mark historical `docs/mcp-vmuse/mcp-protocol-mapping.md`.
4. If VMuse source is changed, sync app resource copies through existing resource-hygiene workflow.

## Test Evidence

Focused tests passed in child results:

- Shell/artifact contract: `11 passed`.
- Runtime artifact/history replay and Cortex projection groups: `6 + 57 + 17 passed`.
- Display current-round image projection: `17 passed`.

## Result

`P722` discovery is complete. The active shell/display/context projection path matches the intended design. The next work should be implementation cleanup of the exact remediation candidates rather than further broad discovery.
