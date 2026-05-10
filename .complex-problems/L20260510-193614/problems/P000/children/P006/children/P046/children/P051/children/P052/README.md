# Phase 5B3.1 Compatibility Residue Audit Map

## Problem

Before deleting or renaming compatibility wrappers, we need a precise source/test inventory of `compat`, `compatibility`, `legacy`, `fallback`, and broad projection helpers. The current hit list mixes legitimate schema migrations, guard tests, current adapters, stale comments, and potentially removable wrappers.

## Success Criteria

- Record a categorized audit of all relevant Cortex source/test hits.
- Identify which hits are legitimate current mechanisms and which require deletion/rename.
- Specifically classify `step_result_projection.format_for_llm`, `novaic_cortex.__init__` exports, and tests importing broad projection helpers.
- Produce a concrete execution map for the following cleanup child problems.
- No source code changes are required beyond the result artifact for this audit problem.
