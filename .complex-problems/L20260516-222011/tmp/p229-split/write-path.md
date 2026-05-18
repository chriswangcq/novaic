# Audit tool step write path durable payload refs

## Problem

The tool/step write path must store heavy tool output as durable payload records and preserve `step_ref`/`payload_ref` metadata instead of embedding raw large results in normal step records.

This belongs under `P229` because write-time storage is the first boundary that determines whether later context assembly can stay pointer-based.

## Success Criteria

- Active tool handler to Cortex write path is mapped with file/function pointers.
- Step write implementation evidence shows `payload_ref`/`step_ref` are required, generated, or preserved for heavy tool output.
- Tests or focused probes verify durable payload refs are emitted for representative shell/display-like output.
