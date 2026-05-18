# P136 success check

## Summary

P136 is successful. The split result R165 closes the full `step_ref` / `payload_ref` mapping problem across runtime creation, Cortex persistence, formatted LLM projection, and regression coverage. The contract is now explicit enough to prevent the previous failure mode where raw or externalized payloads could leak back into context or where a final `payload_ref` could be mistaken for stable step identity.

## Evidence

- P176/C175 proves runtime wrappers emit stable `step_ref`, public `content`, durable payload data, and artifacts without making the runtime layer the final payload-ref authority.
- P177/C176 proves Cortex `write_step`, index, manifest, context-event write, and read paths preserve stable lookup identity while allowing actual payload externalization.
- P178/C177 proves formatted step reads use stable step lookup and only inject display/media through explicit current display perception.
- P179/C178 proves cross-layer regression coverage exists for externalized payload refs, public truncation/manifest behavior, and no historical media reinjection.
- R165 consolidates the child checks and includes passing focused test evidence from all four layers.

## Criteria Map

- Runtime tool result creation paths and Cortex projection handling of `step_ref`/`payload_ref` are mapped: satisfied by P176, P177, and P178.
- Stable `step_ref` versus actual/externalized `payload_ref` contract is documented: satisfied by R165 summary and child result/check bodies.
- Tests prove externalized payloads keep stable step lookup refs while recording blob payload refs: satisfied by P177/P178/P179 test inventories and passing suites.
- Ambiguous or duplicate key handling is fixed or split into focused follow-up: satisfied. The suspicious fallbacks were audited in P179 and classified active-safe; no stale branch was found that required a follow-up.

## Execution Map

- T164 was correctly split into P176-P179 rather than one-goed.
- Each child problem produced a result and success check before the parent result was recorded.
- Parent result R165 summarizes those closed child results and does not introduce unverified new claims.

## Stress Test

The plausible failure mode is a display or shell tool step whose payload is large/media-like and therefore externalized; later context assembly must still find the step by stable `step_ref`, read the final stored payload by final `payload_ref`, and avoid injecting raw base64 into historical/public tool context. The child tests cover this path with externalized payloads, display projection, and no historical image injection.

## Residual Risk

- Non-blocking: Some fallback expressions still require care during future cleanup because they look like compatibility code. They are not current correctness risks and are covered by tests.

## Result IDs

- R165
