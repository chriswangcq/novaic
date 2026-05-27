# Render same-row streaming reasoning updates in the App monitor

## Problem

The App already reads `agent-activity-records` from Entangled, but timeline autoscroll and rendering were built mostly around newly appended rows. Same-row reasoning updates must feel live without introducing a new frontend transport.

## Success Criteria

- Running reasoning rows render with the existing public title contract.
- Same-row text/status updates trigger bottom-follow behavior when the user is near the bottom.
- The App continues to use Entangled cache/query invalidation rather than a new stream channel.
- Tests cover updated timeline projection/render behavior.
