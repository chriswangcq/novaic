# Verify App Entangled activity contract remains the streaming data path

## Problem

The App must keep using `agent-activity-records` from Entangled for streaming reasoning updates and should not introduce a parallel frontend stream channel.

## Success Criteria

- Activity record entity/type supports `public_title`, `status`, `text`, and timestamps needed for streaming updates.
- No new App websocket/SSE/EventSource path is introduced for reasoning streaming.
- Focused entity contract tests remain green.
