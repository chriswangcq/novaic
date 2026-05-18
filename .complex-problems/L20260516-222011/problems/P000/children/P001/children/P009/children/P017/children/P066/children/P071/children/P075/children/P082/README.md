# Scan and clean MCP/VMuse adapter residue

## Problem
MCP/VMuse adapter code may still mention direct agent tools, old subagent spawn surfaces, raw media payloads, or compatibility paths after the shell CLI migration.

## Success Criteria
- Active MCP/VMuse adapter code has no unclassified direct-tool or legacy-residue markers.
- Any remaining marker is current behavior or test-only guard vocabulary.
- Focused tests/import checks for touched MCP/VMuse code pass.
