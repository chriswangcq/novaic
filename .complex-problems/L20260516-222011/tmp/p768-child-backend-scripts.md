# App backend script and launch wiring discovery

## Problem

Discover whether app backend launch scripts, packaging scripts, and development orchestration still launch stale VMuse/FastMCP/direct-media entrypoints or bypass the intended shell/blob/display contract. This belongs under P768 because scripts can override otherwise-clean Rust route wiring.

## Success Criteria

- Relevant scripts under `novaic-app/scripts`, app package scripts, and Tauri backend launch helpers are discovered with bounded commands.
- Hits for VMuse, FastMCP, http server, devicectl, display, screenshot, Blob, Sandbox, LogicalFS, shell, and artifact are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No script/package files are modified in this discovery child.
