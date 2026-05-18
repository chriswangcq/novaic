# Delete stale projection helper and export residue

## Problem

The stale `resolve_for_llm` helper can inline image/base64 payloads into text-oriented LLM context. Once caller verification proves it is dead in production, remove the helper, any now-unused imports, and any package exports that point to it.

## Success Criteria

- Stale helper code is physically removed from production files.
- Unused imports/exports left by the deletion are removed.
- Remaining production projection APIs still import cleanly.
- Focused Cortex projection tests pass after deletion.
