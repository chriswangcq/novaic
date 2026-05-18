# Cortex current display projection contract

## Problem

Audit Cortex display step projection for current-round display results. The projection must expose media as structured display/media metadata for current perception, while historical/tool-message text remains bounded and placeholder-like.

## Success Criteria

- Map display parsing and formatting functions in `novaic-cortex/novaic_cortex/step_result_projection.py` and `step_result_client.py`.
- Prove current display projection produces display/media content separate from plain text.
- Prove historical display projection remains manifest/text-only and does not rehydrate raw images.
- Fix or create follow-up work for any Cortex projection branch that mixes raw base64 into text.

