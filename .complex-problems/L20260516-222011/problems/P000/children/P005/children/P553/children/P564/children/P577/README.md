# Legacy Base64 And Multimodal Compatibility Residue Inventory

## Problem

Search for stale base64, screenshot, data URI, image_url, multimodal compatibility, and provider adapter branches that may bypass the current artifact/display contract. This belongs under P564 because old compatibility paths can silently reintroduce raw media text even after the primary shell/display path is fixed.

## Success Criteria

- Records exact scan commands and outputs for base64/data URI/image_url/multimodal/provider compatibility terms.
- Reads relevant code/test slices with line references.
- Classifies hits as intended provider API formatting, risky raw-history injection, removable old compatibility, or follow-up.
- Identifies whether any legacy branch is still reachable from active runtime/tool paths.
- Captures any high-confidence risky residue for P554 remediation.
