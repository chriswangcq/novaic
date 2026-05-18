# Audit Cortex workspace step payload persistence

## Problem

Cortex workspace persistence must create or preserve durable payload records for tool steps and expose compact `step_ref`/`payload_ref` metadata in step records instead of storing raw heavy results as normal context content.

This belongs under `P231` because workspace persistence is the canonical storage layer for tool step payload refs.

## Success Criteria

- Workspace payload write/read and step write functions are mapped with file/function pointers.
- Evidence shows active step write requires or receives payload/payload_ref and writes durable payload records for heavy content.
- Focused Cortex tests verify step write/index records include `payload_ref`/`step_ref` behavior.
