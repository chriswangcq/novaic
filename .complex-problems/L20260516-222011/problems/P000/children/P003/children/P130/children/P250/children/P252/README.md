# Cortex and shell CLI media residue classification

## Problem
Classify media/base64 residue in `novaic-cortex` and shell-facing CLI/help code. Fix stale command paths or help text that could cause raw image/base64 output into shell text.

## Success Criteria
- Cortex scans cite all relevant residue clusters.
- Shell/devicectl help and command outputs steer media to blob artifact manifests.
- Payload inspection APIs remain bounded pointer-based reads, not raw dump paths.
