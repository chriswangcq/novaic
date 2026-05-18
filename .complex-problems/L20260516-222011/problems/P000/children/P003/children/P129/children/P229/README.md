# Audit payload write and normal context assembly boundaries

## Problem

Tool/step write paths should store large outputs by payload reference, while normal context assembly should use compact projections rather than full payload reads.

## Success Criteria

- Tool/step write path records `step_ref`/`payload_ref` evidence.
- Normal LLM context expansion path does not call full payload read by default.
- Large shell/display raw data stays behind durable payload or explicit payload APIs.
