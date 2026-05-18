# PR-196C — Runtime README / Entrypoint Wording

| Field | Value |
|---|---|
| Status | Done |
| Parent | [PR-196](PR-196-runtime-queue-gateway-centric-doc-cleanup.md) |
| Repo | novaic-agent-runtime |

## Task

Update Runtime README, `main_novaic.py`, and LLM handler docstrings/comments so the collaborators are current:

- Queue Service owns queue/session state.
- Business owns product/internal APIs and LLM config lookup.
- Cortex owns work trace/context.
- LLM Factory owns provider calls.
- Gateway is only a broadcast/signaling edge parameter where still present.

## Tests / Checks

- Grep active Runtime source for “所有 Worker 通过 Gateway” and “LLM config from Gateway”.
- Run a syntax/import smoke if source comments near imports are touched.

## Result

Runtime README, entrypoint banner, LLM handler docstring, and Business prompt default comments now name Queue/Business/Cortex/Factory as collaborators.
