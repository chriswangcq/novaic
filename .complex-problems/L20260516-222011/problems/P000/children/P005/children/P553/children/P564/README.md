# Runtime Display Tool Output Projection Residue Inventory

## Problem

Search agent-runtime and Cortex projection code for stale base64, display, artifact, payload, and multimodal compatibility paths that could put media bytes into public shell/history context or bypass the current `tool-output.v1` manifest contract. This belongs under P553 because shell/display contract regressions were a recent failure mode.

## Success Criteria

- Records exact static scan commands and outputs.
- Classifies base64/display/artifact/tool-output hits as intended, risky, removable, or follow-up.
- Separates valid current-turn `display_perception` image delivery from invalid historical/shell image injection.
- Captures any high-confidence risky residue for P554 remediation.
