# Add near-integrated screenshot/display regression test

## Problem

Add the smallest regression that simulates shell screenshot artifact manifest, subsequent display current perception, and later historical display replay.

## Success Criteria

- Test uses explicit fake Cortex bridge responses by tool call and projection.
- Test proves shell manifest stays text-only with artifact display access hint.
- Test proves current display injects provider-native image content.
- Test proves later historical display replay does not inject image content or raw base64.
- Test fails meaningfully if current/historical projection regresses.
