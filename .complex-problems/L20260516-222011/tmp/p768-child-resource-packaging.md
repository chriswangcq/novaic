# App resource packaging and generated asset wiring discovery

## Problem

Discover whether app resource packaging/generation wiring copies, references, or ships stale VMuse/Sandbox/Blob/LogicalFS resource paths in ways that could preserve old behavior after source cleanup. This belongs under P768 because resource packaging decides what runtime bits reach the app bundle.

## Success Criteria

- Relevant resource copy, generated asset, and packaging wiring files are discovered with bounded commands.
- Hits for copied VMuse resources, FastMCP entrypoints, http server entrypoints, Blob, Sandbox, LogicalFS, display, and screenshot are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No resource/package wiring files are modified in this discovery child.
