# PR-148 — Remove LLM Factory Model Fallback / Failover Branch

| Field | Value |
| --- | --- |
| Status | `[ ]` |
| Owner | Codex |
| Created | 2026-05-01 |
| Repos | novaic-llm-factory, docs |
| Depends on | PR-147 |

## Goal

Remove model-level fallback/failover from the LLM Factory unless a current product owner can name a concrete product value. Keep retry for the selected provider/model if it remains useful, but do not silently switch models behind the Agent.

## Why This Matters

Fallback models make LLM behavior harder to reason about: the Agent asks for one model but may receive another. The scan found `fallback_models` only defined and consumed inside Factory, with no current upstream caller. That is live code complexity with unclear product value.

## Current Suspects

- `novaic-llm-factory/factory/routes/chat_routes.py`
  - `FactoryExtras.fallback_models`
  - fallback provider construction
  - `is_fallback` metadata
- `novaic-llm-factory/factory/retry.py`
  - `fallback_providers`
  - multi-provider attempts queue
- Factory tests and docs that mention fallback/failover.

## Implementation Plan

1. [ ] Remove `fallback_models` from request extras.
2. [ ] Remove fallback provider construction from chat route.
3. [ ] Simplify `RetryExecutor` to retry only the selected provider/model.
4. [ ] Remove `is_fallback` response/log metadata or replace with a hard-coded absent field.
5. [ ] Add guardrail that `fallback_models`, `fallback_providers`, and `is_fallback` cannot reappear in active Factory code.

## Unit / Guardrail Tests

- [ ] Factory retry tests cover retry of the selected provider only.
- [ ] Factory route tests reject or ignore old `fallback_models` according to the chosen API contract.
- [ ] Guardrail grep catches fallback/failover reintroduction.

## Smoke / Deploy

- [ ] Factory tests pass.
- [ ] Runtime LLM call smoke passes against Factory.
- [ ] Deploy Factory.
- [ ] Production smoke: normal chat call logs exactly one selected model path.
- [ ] Production log evidence: no `is_fallback` / failover event in new calls.

## Git / Merge

- [ ] Commit in `novaic-llm-factory`.
- [ ] Parent repo submodule bump / docs commit.
- [ ] Push `main`.
- [ ] Mark this ticket `[deployed]` only after deploy evidence is collected.

