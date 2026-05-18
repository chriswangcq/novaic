# App Backend Startup Graph Cleanup Result

## Summary

Completed the app backend startup graph audit and remediation. The scripts/config now consistently represent the current backend graph: packaged storage uses `novaic-storage-a`, app config exposes `cortex:19996`, the dev startup script treats Cortex as an external dependency, and stale VMuse MCP URL config is gone.

## Done

- P804/R785 audited scripts, config, ports, and binary expectations.
- P805/R791 remediated:
  - packaged blob/storage binary contract
  - source resource `novaic-storage-a` presence
  - dev startup Cortex URL naming
  - app `services.json` Cortex/vmcontrol conflict
  - stale `runtime.vmuse_mcp_url`
  - resource/generated startup script/config synchronization

## Verification

- P804 audit evidence covered the pre-change topology.
- P805 final verification covered:
  - `bash -n` for all committed startup scripts
  - `python -m json.tool` for both app service config copies
  - `cmp -s` for resource/generated packaged scripts, configs, and `novaic-storage-a`
  - `diff -qr` over resource/generated backend directories
  - targeted residue scan for `PORT_CORTEX`, `vmuse_mcp_url`, `8080/mcp`, `$BACKENDS_DIR/novaic-blob-service`, and old blob startup text

## Known Gaps

- Existing historical backend binary tracking remains uneven: generated assets track backend binaries while resource backend binaries are partly ignored. The startup contract-critical `novaic-storage-a` is now present in resources and must be staged.

## Artifacts

- P804 result R785.
- P805 result R791.
