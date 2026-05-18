# Display current-round LLM image projection discovery

## Problem

Discover how the display tool consumes Blob/artifact references and how current-round displayed images are projected into LLM requests. This must verify whether images are sent through the model API as image content rather than serialized base64 text.

## Success Criteria

- Display tool handler/executor code is identified with file pointers.
- LLM request construction path for display image projection is identified with file pointers.
- Tests or logs proving current-round image projection behavior are identified where present.
- Any active path that converts displayed images into text/base64 in LLM messages is listed as a remediation candidate.
