# Agent loop prepare-path proof

## Problem

The current LLM request assembly path must be proven to use the authoritative event/source snapshot path rather than stale materialized context projection endpoints.

## Success Criteria

- The live agent loop path from inbound message/session to LLM request creation is traced with source slices.
- The role of `prepare_for_llm`, context event snapshots, active skill stack injection, and tool observation projection is documented.
- Tests or guards prove the LLM prepare path does not call `/v1/context/read` as its source of history.
- Any stale live path discovered is fixed or split.
