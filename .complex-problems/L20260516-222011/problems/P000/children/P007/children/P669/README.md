# Runtime health and log access observability audit

## Problem

Inspect health endpoints, runtime log access paths, LLM factory log APIs/UI, and related observability code for stale contracts or poor diagnostics. Optimize low-risk failures such as broken fetch paths, empty details, missing error text, or stale endpoint assumptions.

## Success Criteria

- Health/log/LLM-factory observability routes, clients, and UI components are located and inspected.
- Current request/response contracts are checked against tests or local static evidence.
- Any concrete low-risk diagnostics or contract gaps are fixed.
- Relevant tests or local checks are run and evidence is recorded.
