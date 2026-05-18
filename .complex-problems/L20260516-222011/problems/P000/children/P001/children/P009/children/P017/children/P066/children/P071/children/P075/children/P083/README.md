# Scan and clean Cortex shell CLI adapter residue

## Problem
Cortex shell capability code owns `agentctl`, `devicectl`, payload access, and media/artifact shell contracts. It must not keep stale direct-tool, base64-as-text, or compatibility code paths after the new shell/display/blob contract.

## Success Criteria
- Active Cortex shell CLI code matches current terminal-text plus artifact-manifest contract.
- Direct-tool leftovers are removed or classified as guard/blocked vocabulary.
- Focused Cortex shell/tool projection tests pass.
