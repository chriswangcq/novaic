# Phase 3.4: Cut tool step recording to events

## Problem

Tool call/result observations are currently persisted as legacy `steps/*.json`, `steps/_index.jsonl`, and payload records. The authoritative fact must become `ToolStepRecorded` ContextEvents, with payload bytes still stored through the explicit payload/blob path when needed.

## Success Criteria

- `/v1/steps/write` appends `ToolStepRecorded` events.
- Event payloads preserve call id, tool name, status, observation preview/summary/head, payload ref, and scope id.
- Legacy step files, if still created, are projection/debug artifacts only.
- Tests verify event stream content and no hidden payload file read is required for projection.
