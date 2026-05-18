# App VMuse copied resource sync discovery result

## Summary

The two app VMuse copy trees were scanned and compared with source VMuse. They exactly mirror the source VMuse files, including the stale FastMCP direct media entry path in `main.py` and FastMCP CLI path in `cli.py`. No app resource or generated copy files were modified.

## Done

- Discovered copied VMuse files under `novaic-app/src-tauri/resources/novaic-mcp-vmuse`.
- Discovered copied VMuse files under `novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse`.
- Searched copied trees for FastMCP, ImageContent, base64, screenshot, display, blob, tool-output, and HTTP server terms.
- Compared checksums for representative source/copy files.

## Verification

- Scan artifact: `.complex-problems/L20260516-222011/tmp/p767-vmuse-copy-scan.txt`.
- `main.py`, `cli.py`, `http_server.py`, `__init__.py`, `pyproject.toml`, and `run_server.sh` are byte-identical between source VMuse and both app copy trees.
- Copied `main.py` imports FastMCP/Image and returns direct MCP image content for screenshot/aim/browser screenshot.
- Copied `cli.py` still advertises/starts FastMCP.
- Copied `http_server.py` and VMuse lower-level tools use base64 for lower-level HTTP/media transport; this is not by itself the stale LLM-context path.

## Known Gaps

- Remediation candidate: when source VMuse removes or hard-disables the old FastMCP direct media path, synchronize the cleanup into both copy trees:
  - `novaic-app/src-tauri/resources/novaic-mcp-vmuse/src/novaic_mcp_vmuse/main.py`
  - `novaic-app/src-tauri/resources/novaic-mcp-vmuse/src/novaic_mcp_vmuse/cli.py`
  - `novaic-app/src-tauri/resources/novaic-mcp-vmuse/src/novaic_mcp_vmuse/__init__.py`
  - `novaic-app/src-tauri/resources/novaic-mcp-vmuse/pyproject.toml`
  - `novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse/src/novaic_mcp_vmuse/main.py`
  - `novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse/src/novaic_mcp_vmuse/cli.py`
  - `novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse/src/novaic_mcp_vmuse/__init__.py`
  - `novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse/pyproject.toml`
- No app resource or generated copy files were modified in this discovery child.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p767-vmuse-copy-scan.txt`
