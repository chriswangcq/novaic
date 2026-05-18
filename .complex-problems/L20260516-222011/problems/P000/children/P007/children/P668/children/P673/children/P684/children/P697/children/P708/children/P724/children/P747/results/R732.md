# Post-remediation media-boundary scan result

## Summary

Ran focused post-remediation scans. The removed Device Service screenshot route is absent. Remaining media/base64/display hits are classified as current shell/display contract, provider-native current-round image transport, lower-level VmControl/VMuse protocol, test/UI guard, auth/cursor/guest-agent encoding, or current/historical documentation. No active unclassified large-media-as-text leak was found.

## Commands

```bash
rg -n '@router\.post\("/vms/\{vm_id\}/screenshot"|/api/vmcontrol/vms/.*/screenshot|/api/vmcontrol/vms/\{vm_id\}/screenshot|def screenshot\(vm_id' \
  novaic-device docs novaic-app novaic-cortex novaic-agent-runtime novaic-mcp-vmuse scripts \
  -g '!**/.venv/**' -g '!**/node_modules/**' -g '!**/target/**' || true

rg -n "base64|data:image|_mcp_content|tool-output\.v1|runtime-artifact|blob://|image_ref|display_perception|screenshot" \
  novaic-device/device novaic-cortex/novaic_cortex novaic-agent-runtime/task_queue \
  novaic-mcp-vmuse/src docs scripts novaic-app/src novaic-app/src-tauri/vmcontrol/src \
  -g '*.py' -g '*.md' -g '*.ts' -g '*.tsx' -g '*.rs' -g '*.sh' \
  -g '!**/.venv/**' -g '!**/node_modules/**' -g '!**/target/**' | head -400
```

## Classifications

### Removed Route

- `POST /api/vmcontrol/vms/{vm_id}/screenshot`: no hits in the targeted route scan.

### Current Contract

- `novaic-cortex/novaic_cortex/shell_capabilities.py`
  - Decodes Device screenshot/file-pull base64 internally and emits Blob `tool-output.v1` manifests.
- `novaic-cortex/novaic_cortex/step_result_projection.py`
  - Keeps history/current projections bounded; display perception can carry `image_ref`.
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
  - `display` stores public placeholder/history and durable `image_ref`; inline image bytes are only for current display perception.
- `novaic-agent-runtime/task_queue/utils/multimodal.py`
  - Converts current display perception to provider-native image content.

### Lower-Level Protocols

- `novaic-app/src-tauri/vmcontrol/src/api/routes/screen.rs`
- `novaic-app/src-tauri/vmcontrol/src/api/routes/hd_tools.rs`
- `novaic-app/src-tauri/vmcontrol/src/api/routes/mobile.rs`
- `novaic-app/src-tauri/vmcontrol/src/api/routes/browser.rs`
- `novaic-mcp-vmuse/src/novaic_mcp_vmuse/tools/desktop.py`
- `novaic-mcp-vmuse/src/novaic_mcp_vmuse/tools/browser.py`
- `novaic-mcp-vmuse/src/novaic_mcp_vmuse/tools/files.py`
- `novaic-mcp-vmuse/src/novaic_mcp_vmuse/http_server.py`

These are Device/VmControl/VMuse lower-level media/file protocols. Current Cortex shell wrappers normalize HD shell-facing outputs to Blob manifests before LLM history.

### Non-Media or Guard/Doc Hits

- WebRTC cursor `rgba_base64`: cursor transport, not LLM shell/history.
- Coturn/WebRTC auth base64 and Cortex auth base64: auth/encoding, not media output.
- App ActivityTimeline/base64 tests and guards: intentional protection.
- Blob docs: current or historical notes explicitly saying old JSON/base64 upload paths are deleted.
- `docs/mcp-vmuse/mcp-protocol-mapping.md`: updated to current historical/current boundary language.

## Result

Scan sweep passed. No new active remediation item was found.
