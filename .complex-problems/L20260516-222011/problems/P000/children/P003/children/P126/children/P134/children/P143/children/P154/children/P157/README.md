# Runtime LLM prepare caller authority

## Problem

Runtime LLM call assembly must invoke Cortex prepare/read-model APIs rather than `context/read` projection APIs when constructing provider messages.

This belongs under `P154` because even a correct Cortex endpoint is insufficient if runtime calls a different legacy API.

## Success Criteria

- Runtime prepare-context caller and LLM assembly path are mapped.
- Evidence proves runtime uses `/v1/context/prepare_for_llm` or the explicit prepare contract.
- Evidence proves runtime LLM assembly does not call `read_context` as authority.
