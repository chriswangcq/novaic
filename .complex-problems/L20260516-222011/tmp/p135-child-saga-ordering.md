# Runtime saga prepare-context ordering map

## Problem

The ReAct queue saga decides when `prepare_context` runs relative to message reads, tool result persistence, and `llm.call`. The ordering must be mapped so the final LLM call cannot accidentally use stale state from a previous step or wake.

## Success Criteria

- `novaic-agent-runtime/task_queue/sagas/react_think.py` is mapped for prepare-context step ordering and dependencies.
- The dependency handoff from previous saga result into `llm.call` is documented with source pointers.
- Any ordering branch that can skip prepare-context while still calling the LLM is classified as active-safe, dead, or stale.
- Focused tests or static guards covering prepare-before-LLM ordering are identified or added.
