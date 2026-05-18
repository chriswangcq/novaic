# Audit Cortex event projection preserves payload pointers

## Problem

Cortex event streams and projections must preserve compact pointer metadata (`step_ref`, `payload_ref`, artifacts/projection summaries) without expanding durable payload bodies into normal event/context records.

This belongs under `P229` because event projection is the middle layer between durable write storage and runtime context preparation.

## Success Criteria

- Event writer/projection paths are mapped with file/function pointers.
- Projection behavior is shown to preserve refs and compact summaries rather than full payload bytes/text.
- Focused event projection tests pass or are added if coverage is missing.
