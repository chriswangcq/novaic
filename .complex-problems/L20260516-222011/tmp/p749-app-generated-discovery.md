# App resource and generated asset semantic residue discovery

## Problem

Audit app resource copies and generated assets for semantic residue while distinguishing source-of-truth files from synchronized generated copies.

## Success Criteria

- Scans cover `novaic-app` resource and generated asset locations relevant to VMuse, Device, display, and shell tooling.
- Findings distinguish generated copies from source-of-truth code and docs.
- Required sync/remediation candidates are listed for the remediation child.
- No generated assets are manually patched in this discovery child.
