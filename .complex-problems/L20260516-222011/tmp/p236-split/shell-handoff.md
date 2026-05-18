# Audit runtime shell handoff uses compact projection plus durable payload

## Problem

The runtime shell path must expose terminal-like bounded text to the LLM while preserving raw command output as durable payload/artifact data where needed. It must not pass huge stdout/base64 as ordinary tool message text.

This belongs under `P236` because shell is the primary interface tool and the concrete regression source for oversized tool context.

## Success Criteria

- Runtime shell handler/projection code is mapped with file/function pointers.
- Evidence shows public shell result text is bounded/terminal-like and raw output is separated as durable payload or artifact metadata.
- Focused shell projection/runtime tests pass.
