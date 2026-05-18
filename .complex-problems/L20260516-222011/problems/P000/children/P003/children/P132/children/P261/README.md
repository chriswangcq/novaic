# Near-integrated screenshot manifest to display replay regression

## Problem

Local Cortex and runtime tests can pass independently while the real flow still breaks. Add or verify a near-integrated regression that models shell screenshot artifact manifest output, explicit display/current media projection, and later historical replay without raw base64 text leakage.

## Success Criteria

- A near-integrated test exists or is added for screenshot manifest -> display/current projection -> historical replay.
- The test uses realistic `tool-output.v1` and/or `tool-step-payload.v1` shapes.
- The test asserts the display/current path has image media only when explicit display perception is selected.
- The test asserts later history replay contains no raw base64/data URL text.
