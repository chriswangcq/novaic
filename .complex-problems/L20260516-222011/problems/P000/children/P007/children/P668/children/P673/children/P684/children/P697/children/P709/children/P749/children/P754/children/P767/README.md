# App VMuse copied resource sync discovery

## Problem

Discover whether `novaic-app` VMuse resource/generated copies preserve stale FastMCP/direct media behavior or diverge from the source VMuse cleanup candidates. This belongs under P754 because app-bundled copies can ship stale behavior even if source VMuse is cleaned.

## Success Criteria

- VMuse resource/generated copy files are discovered with bounded commands.
- Direct media/FastMCP/base64/display hits are classified as copied source residue, current lower-level VMuse transport, or unrelated generated vocabulary.
- Required source-to-copy synchronization/remediation candidates are listed.
- No app resource/generated files are modified in this discovery child.
