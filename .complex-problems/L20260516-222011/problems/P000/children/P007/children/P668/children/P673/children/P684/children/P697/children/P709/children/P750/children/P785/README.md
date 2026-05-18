# App Resource Generated Asset And Backend Startup Remediation

## Problem

Synchronize app resource/generated copies and fix stale App backend startup/package graph residue without creating source/generated divergence.

## Success Criteria

- VMuse source cleanup is synchronized into `novaic-app/src-tauri/resources/novaic-mcp-vmuse` and generated Apple asset copies when those copies remain committed.
- `novaic-app/scripts/start-backends.sh`, packaged backend scripts, and generated backend scripts reflect the current service topology or are explicitly marked dev-only if that is the correct role.
- `PORT_CORTEX=19996` versus `vmcontrol` port naming conflict is resolved.
- Backend binary/resource expectations match the scripts.
- Stale HD tools screenshot-to-LLM comment in VmControl Rust code is updated.
- Focused script/config checks run for startup/package graph.
