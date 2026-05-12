# Cortex display projection must not hide missing media as OK

## Problem

Cortex `display_perception` projection currently uses a generic fallback that can produce `{"type":"text","text":"OK"}` when no text or display media is found. For display perception this is too ambiguous: it can hide a broken media projection and make Factory logs look successful while no image was delivered.

## Success Criteria

- `display_perception` projection for empty parsed content returns a diagnostic text marker instead of plain `OK`.
- Normal history/current tool projections can keep their existing text behavior if needed.
- Tests prove empty display projection is distinguishable from a successful image projection.
