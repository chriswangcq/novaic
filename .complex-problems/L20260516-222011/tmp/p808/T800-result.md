# VMuse Runtime URL Config Contract Result

## Summary

Removed stale `runtime.vmuse_mcp_url` from both app service config copies. No active in-repo consumer of `vmuse_mcp_url` or `8080/mcp` was found, so the field was inactive residue rather than an active transport contract.

## Done

- Updated `novaic-app/src-tauri/resources/config/services.json`.
- Updated `novaic-app/src-tauri/gen/apple/assets/config/services.json`.
- Removed `runtime.vmuse_mcp_url`.

## Verification

- Active consumer scan:
  - `rg -n "vmuse_mcp_url|8080/mcp" novaic-app novaic-agent-runtime novaic-gateway novaic-cortex scripts ...`
  - no remaining matches after removal.
- JSON validity:
  - `python -m json.tool` for both service config copies.
- Config synchronization:
  - `cmp -s` confirmed resource and generated config copies are identical.
- Remaining `/mcp` scan shows only intentional non-config references:
  - gateway dynamic MCP route comments
  - VMuse virtio serial port path `/dev/virtio-ports/mcp`

## Known Gaps

- `novaic-app/scripts/sync-vmuse-resource.sh` still contains a stale `main.py` source check found during broader VMuse scanning, but it is not the runtime URL config field. This should be handled by the final app resource/generated hygiene phase if not already covered.

## Artifacts

- Modified both service config JSON files.
