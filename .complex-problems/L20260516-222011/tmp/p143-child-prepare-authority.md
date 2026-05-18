# LLM prepare path context authority audit

## Problem

The active LLM prepare-context path must not read `context.jsonl` as authoritative conversation context. It should use ContextEvent/read-model projections. This audit must prove the current prepare path authority.

This belongs under `P143` because it is the highest-risk source of duplicate/stale context and payload leakage.

## Success Criteria

- Active prepare-context/read-model path is mapped with source pointers.
- Evidence proves it does not call `read_context` or parse `context.jsonl` as authority.
- If any authority read exists, it is fixed or split into a blocking child problem.
