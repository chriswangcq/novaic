# Blob LogicalFS Sandbox VMuse service-code residue discovery

## Problem

Discover semantic residue in Blob, LogicalFS, Sandboxd, Sandbox SDK, VMuse, and VmControl-related source code that could imply wrong file authority, byte ownership, process execution ownership, or direct media projection behavior.

## Success Criteria

- Scans cover `novaic-blob-service`, `novaic-logicalfs`, `novaic-sandbox-service`, `novaic-sandbox-sdk`, `novaic-mcp-vmuse`, and relevant app/vmcontrol source surfaces when needed.
- Findings distinguish intentional lower-level byte/media protocols from shell/history/display leakage risks.
- Exact remediation candidates are listed.
- No code is modified in this discovery child.
