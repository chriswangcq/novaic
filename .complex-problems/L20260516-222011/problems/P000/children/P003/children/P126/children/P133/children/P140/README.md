# ContextEvent read model and budget boundary map

## Problem

`ContextEventReadModel.prepare` turns pure projection output into prepared LLM context with budget compaction and top-first stack normalization. That boundary must be verified separately from raw event projection.

## Success Criteria

- Read-model behavior for empty roots, projection, budget compaction, token counting, usage ratio, and top-first stack normalization is documented.
- Read-model tests are identified and run.
- Any implicit fallback to old context assembly is classified and fixed or split.
