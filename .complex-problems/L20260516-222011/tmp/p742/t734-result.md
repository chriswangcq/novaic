# VMuse protocol mapping doc patch result

## Summary

Patched `docs/mcp-vmuse/mcp-protocol-mapping.md` to mark direct Runtime/VMuse MCP media exposure as historical and document the current shell / Blob / display boundary.

## Changes

- Replaced the stale "Runtime directly introduces VMuse tool list to LLM" live-design language with a historical section.
- Added the current live path:
  - VMuse / Device perform capture/action.
  - Cortex shell converts media bytes into Blob artifacts.
  - shell stdout returns terminal text plus `tool-output.v1` manifests.
  - history replay remains manifest-only.
  - `display` is the explicit current-round visual perception path.
- Stated that Runtime should not use VMuse media tools as the direct LLM media entrypoint.

## Verification

Commands run:

```bash
sed -n '1,260p' docs/mcp-vmuse/mcp-protocol-mapping.md
rg -n "直接引入即用|清单.*倒给 LLM|图片或者成功信号套个标准|直接.*LLM|base64|tool-output\\.v1|display|manifest-only" docs/mcp-vmuse/mcp-protocol-mapping.md
```

The old exact stale phrases no longer appear. Remaining `base64`, `tool-output.v1`, `display`, `manifest-only`, and `直接给 LLM` mentions are part of the new warning/current-contract wording.

## Result

Documentation-only remediation complete.
