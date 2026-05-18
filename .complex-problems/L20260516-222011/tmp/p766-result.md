# App resource copy residue discovery result

## Summary

App-bundled resource and generated asset copies were scanned for mirrored Sandbox/VMuse/LogicalFS/Blob residue. A high-priority copied-residue remediation candidate was found: both app resource copies of VMuse exactly mirror the stale FastMCP direct media entry path found in source VMuse.

## Done

- Discovered app resource/generated copies related to VMuse under:
  - `novaic-app/src-tauri/resources/novaic-mcp-vmuse`
  - `novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse`
- Searched app resource/generated surfaces for `legacy`, `compat`, `fallback`, `direct`, `bypass`, `base64`, `media`, `artifact`, `screenshot`, `display`, `blob`, `raw`, `TODO`, `FIXME`, `stub`, `mcp`, `FastMCP`, `ImageContent`, `main.py`, `http_server`, `logicalfs`, `sandbox`, `writeback`, and `materialize`.
- Compared representative source VMuse files with resource/generated copies using SHA-256 prefixes.

## Verification

- Scan artifact: `.complex-problems/L20260516-222011/tmp/p766-app-resource-scan.txt`.
- Source/copy comparison showed these files are byte-identical between source VMuse and both app copies:
  - `src/novaic_mcp_vmuse/main.py`
  - `src/novaic_mcp_vmuse/cli.py`
  - `src/novaic_mcp_vmuse/http_server.py`
- The copied `main.py` files import FastMCP and `Image`, decode screenshot base64, and return direct MCP image content for screenshot/aim/browser screenshot tools.
- The copied `cli.py` files still advertise and start FastMCP by importing `.main`.
- Large unrelated hits under bundled Android/QEMU resources were classified as unrelated third-party resource vocabulary, not NovaIC service residue.

## Known Gaps

- Remediation candidate: once source VMuse removes or hard-disables the old FastMCP direct media path, synchronize the same cleanup into both copied app resource trees:
  - `novaic-app/src-tauri/resources/novaic-mcp-vmuse/src/novaic_mcp_vmuse/main.py`
  - `novaic-app/src-tauri/resources/novaic-mcp-vmuse/src/novaic_mcp_vmuse/cli.py`
  - `novaic-app/src-tauri/resources/novaic-mcp-vmuse/src/novaic_mcp_vmuse/__init__.py`
  - `novaic-app/src-tauri/resources/novaic-mcp-vmuse/pyproject.toml`
  - `novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse/src/novaic_mcp_vmuse/main.py`
  - `novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse/src/novaic_mcp_vmuse/cli.py`
  - `novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse/src/novaic_mcp_vmuse/__init__.py`
  - `novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse/pyproject.toml`
- No product code was modified in this discovery child. The candidate should be handled by the later remediation branch.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p766-app-resource-scan.txt`
- SHA-256 source/copy comparison output from the discovery command
