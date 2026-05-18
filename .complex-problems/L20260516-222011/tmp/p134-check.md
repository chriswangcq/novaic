# Workspace materialized projections and payload reference map success check

## Summary

`P134` is successful. The split result `R142` is backed by four closed child problems covering payload storage, tool-step/index projection, `context.jsonl` projection authority, and API materialization call sites. The materialized workspace files are now classified as observability/retrieval projections rather than LLM context authority, with focused tests and residue guards covering the plausible regressions.

## Evidence

- `P141/C138` maps `write_payload`, `read_payload`, blob externalization, manifest metadata, and payload failure behavior.
- `P142/C146` maps `normalize_step`, `write_step`, `write_step_projection`, `_index.jsonl` metadata, and active step-write call-site wiring.
- `P143/C154` maps `context.jsonl` helpers/callers and proves active LLM prepare uses the ContextEvent read model rather than the materialized projection.
- `P144/C155` maps Cortex API context/step/payload endpoints and confirms no duplicate active API write path diverges from ContextEvents.
- `R142` aggregates those child results and records the remaining non-blocking API naming risk.

## Criteria Map

- `workspace.py` context append, step write, index write, and payload write/read functions are mapped: satisfied by `P141`, `P142`, and `P143`.
- Tool step write behavior is verified to require payload/payload_ref rather than inline raw result: satisfied by `P142` child coverage, including API and workspace rejection tests.
- `context.jsonl` and context projection write paths are classified as active source, debug projection, compatibility, or stale: satisfied by `P143`, which classifies projection helpers and proves LLM authority is the event read model.
- Tests covering payload externalization, step indexes, and context writes are identified and run: satisfied by child checks `C138`, `C146`, `C154`, and `C155`.
- Any stale or misleading materialized projection path is removed or split for cleanup: satisfied for blocking correctness. The only remaining confusing path is `/v1/context/read` naming, classified as non-blocking clarity debt because guards prevent it from becoming provider-message authority.

## Execution Map

- Parent ticket `T127` was split into `P141` through `P144`.
- Each child closed with a result and success check before `R142` was recorded.
- `R142` summarizes the child results rather than adding new unverified implementation.

## Stress Test

- Plausible failure: raw shell/display payloads leak into `steps/*.json` or provider context. Covered by strict tool-step shape validation, payload externalization/mirroring, and runtime no-historical-tool-image guard suites cited by children.
- Plausible failure: corrupt `context.jsonl` or `_index.jsonl` silently hides data loss. Covered by fail-loud corrupt projection/index tests.
- Plausible failure: old `context.read` projection becomes LLM authority again. Covered by conflicting-snapshot tests and static guards proving final provider messages use `prepare_for_llm`.
- Plausible failure: an unreviewed write path bypasses ContextEvents. Covered by direct-write residue scans and API call-site stress search.

## Residual Risk

- `/v1/context/read` naming remains confusing. It should be considered future API clarity work, but it is not blocking for this workspace projection/payload authority slice.
- This check does not close root-level "all backend optimization" work; it closes only `P134`.

## Result IDs

- R142
