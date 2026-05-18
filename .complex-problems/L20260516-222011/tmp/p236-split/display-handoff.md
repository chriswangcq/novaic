# Audit runtime display and media handoff avoids raw image text

## Problem

The runtime display/media path must present visual artifacts to the model through the correct media/content channel or compact tool result, not as raw base64 text in normal history.

This belongs under `P236` because display/media outputs have different contracts from shell stdout and previously risked raw image text entering context.

## Success Criteria

- Display/media tool result handling and LLM message conversion paths are mapped with file/function pointers.
- Evidence shows normal tool result text is compact and image data is not passed as raw text history.
- Focused display/media tests pass, including no historical tool image/base64 injection.
