# Audit runtime LLM context expansion avoids full payload reads

## Problem

The normal runtime path that prepares LLM messages must not call full payload read APIs or inline durable payload bodies by default. It should request compact formatted step projections/previews for historical tool results.

This belongs under `P229` because runtime context preparation is the final boundary before data enters the model request.

## Success Criteria

- Runtime message expansion path is mapped with file/function pointers.
- Evidence shows default context preparation uses formatted projection APIs, not `/v1/payload/read` or equivalent full durable payload reads.
- Focused runtime tests verify historical shell/display outputs remain compact in LLM request messages.
