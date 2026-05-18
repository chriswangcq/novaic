# LLM handler provider request assembly map check

## Summary

`P169` is solved. The split children prove both provider assembly layers: the pure `LLMCall` contract receives explicit payload messages/tools and the handler delegates to that contract before transport. No active hidden context source reaches provider messages/tools in this boundary.

## Evidence

- `C164`: maps `contracts/llm_call.py:37`, `:44-57`, `:115-146`, and records `13 passed`.
- `C165`: maps `handlers/llm_handlers.py:93`, `:117-127`, `:136-141`, and records `22 passed`.
- `R152`: consolidates child results `R150` and `R151`.

## Criteria Map

- `llm_handlers.py` and `contracts/llm_call.py` mapped: satisfied by `C164` and `C165`.
- Final `messages` and `tools` source documented: satisfied by `C164`; `messages` from explicit payload through injected preprocessing, `tools` from explicit payload.
- Guards prove final request does not use context reads: satisfied by `C165`.
- Focused tests run: satisfied.

## Execution Map

- `T155` split into `P171` and `P172`.
- Both children completed successfully.
- Parent result `R152` recorded.

## Stress Test

If contract-layer tools stop flowing from explicit payload, the new `prepared.tools` assertion fails. If handler reads Cortex context or bypasses `prepare_llm_call`, static guard tests fail.

## Residual Risk

- End-to-end handoff regression coverage across the whole saga remains sibling `P170`.

## Result IDs

- R152
