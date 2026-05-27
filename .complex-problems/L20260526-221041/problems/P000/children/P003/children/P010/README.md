# Update ActivityTimeline for same-record streaming updates

## Problem

`ActivityTimeline` currently follows bottom based mainly on row count/latest key. Streaming reasoning updates mutate the same row's text/status, so the component needs an explicit same-row update key and tests for running reasoning display.

## Success Criteria

- Latest record key includes fields that change during streaming, such as text/status/updated marker.
- Running reasoning rows display `正在思考` and detail text.
- Tests cover public title/projection behavior and same-row update key behavior.
