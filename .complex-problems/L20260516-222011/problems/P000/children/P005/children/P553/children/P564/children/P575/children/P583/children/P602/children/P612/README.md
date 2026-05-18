# UI Monitor and Log Artifact Display Boundary

## Problem

Audit UI monitor/log display surfaces that could present artifact or tool output data, including Agent Monitor and LLM Factory logs, and prove they are bounded/escaped/display-only rather than raw image-byte UI paths.

## Success Criteria

- Records exact scans for monitor/log artifact, raw JSON, request/response body, image, and base64 rendering paths.
- Cites UI/backend static slices that bound or escape display content.
- Reuses P604 evidence where appropriate but explicitly maps it to this broader UI display problem.
- Creates a follow-up if monitor/log UI surfaces render raw unredacted image bytes in normal display paths.
