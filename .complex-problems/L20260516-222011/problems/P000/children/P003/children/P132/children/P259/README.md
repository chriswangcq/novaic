# Cortex projection regression coverage

## Problem

Cortex step result projection is one side of the cross-layer contract. It must prove that `tool-output.v1` artifact manifests, display perception projection, history projection, current non-display projection, and payload pointer behavior are covered by focused tests.

## Success Criteria

- Focused Cortex projection tests pass.
- Tests prove history/current non-display projections do not include raw image/base64 data.
- Tests prove explicit display perception is the only Cortex projection mode allowed to include image media.
- Tests prove shell screenshot artifact manifests remain text/manifest-only until explicit display is requested.
