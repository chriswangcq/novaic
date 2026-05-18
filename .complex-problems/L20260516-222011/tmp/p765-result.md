# VMuse service residue discovery result

## Summary

VMuse service/MCP source, tests, README, and entrypoints were scanned for stale direct media exposure, raw screenshot/base64 stdout, fallback/compatibility, and ownership residue. A high-priority remediation candidate was found: the FastMCP `main.py` and `cli.py` entry path still exists and returns direct MCP `ImageContent` for screenshots/aim/browser screenshots, even though current deployment uses `http_server.py` and the shell Blob artifact plus display perception boundary.

## Done

- Enumerated the VMuse file surface under `novaic-mcp-vmuse`.
- Searched for `legacy`, `compat`, `fallback`, `direct`, `bypass`, `base64`, `media`, `artifact`, `screenshot`, `display`, `blob`, `raw`, `TODO`, `FIXME`, `stub`, `mcp`, `image`, `jpeg`, `png`, `tool-output`, `data_url`, `data url`, and `stdout`.
- Inspected high-signal files:
  - `novaic-mcp-vmuse/src/novaic_mcp_vmuse/main.py`
  - `novaic-mcp-vmuse/src/novaic_mcp_vmuse/cli.py`
  - `novaic-mcp-vmuse/src/novaic_mcp_vmuse/http_server.py`
  - `novaic-mcp-vmuse/src/novaic_mcp_vmuse/__init__.py`
  - `novaic-mcp-vmuse/src/novaic_mcp_vmuse/tools/desktop.py`
  - `novaic-mcp-vmuse/tests/test_contract_markers.py`
  - `novaic-mcp-vmuse/pyproject.toml`
- Ran VMuse tests: `PYTHONPATH=novaic-mcp-vmuse/src pytest -q novaic-mcp-vmuse/tests`.

## Verification

- Scan artifact: `.complex-problems/L20260516-222011/tmp/p765-vmuse-scan.txt`.
- Test result: `1 passed in 0.01s`.
- `http_server.py` is the current deployed route according to `run_server.sh`, app setup routes, and vmcontrol service files. It returns lower-level JSON results, including screenshot base64, to the outer caller; that is current lower-level protocol behavior and should be wrapped by device/runtime into Blob artifacts before LLM context.
- `tools/desktop.py` legitimately captures screenshots and encodes bytes as base64 for VMuse lower-level transport; that is not by itself the shell/LLM leakage path.
- `main.py` imports FastMCP and `Image`, decodes screenshot base64, and returns `[image_content, info_text]` for screenshot/aim/browser screenshot tools. That is a stale direct MCP media exposure path under the current architecture.
- `cli.py` still describes and starts a FastMCP server by importing `.main`.
- `__init__.py` explicitly documents `main.py` as a separate FastMCP entry point.
- `pyproject.toml` exposes `novaic = "novaic_mcp_vmuse.cli:main"`, keeping the stale FastMCP CLI reachable.

## Known Gaps

- Remediation candidate: remove or hard-disable the old FastMCP direct media entry path:
  - `novaic-mcp-vmuse/src/novaic_mcp_vmuse/main.py`
  - FastMCP serve/info/skills behavior in `novaic-mcp-vmuse/src/novaic_mcp_vmuse/cli.py`
  - FastMCP entry wording in `novaic-mcp-vmuse/src/novaic_mcp_vmuse/__init__.py`
  - `novaic-mcp-vmuse/pyproject.toml` console script if it only reaches the old CLI
- Equivalent app resource/generated copies are tracked by the separate app resource child problem.
- No product code was modified in this discovery child. The candidate should be handled by the later remediation branch.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p765-vmuse-scan.txt`
- pytest output: `1 passed in 0.01s`
