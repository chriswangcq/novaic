# PR-148 — Remove LLM Factory Model Fallback / Failover Branch

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
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

1. [x] Remove `fallback_models` from request extras.
2. [x] Remove fallback provider construction from chat route.
3. [x] Simplify `RetryExecutor` to retry only the selected provider/model.
4. [x] Remove `is_fallback` response/log metadata.
5. [x] Add guardrail that `fallback_models`, `fallback_providers`, and `is_fallback` cannot reappear in active Factory code.
6. [x] Remove implicit default-model substitution when requested `model` cannot be resolved.

## Unit / Guardrail Tests

- [x] Factory retry tests cover retry of the selected provider only.
- [x] Factory route tests reject old `fallback_models`.
- [x] Guardrail grep catches fallback/failover reintroduction.

## Smoke / Deploy

- [x] Factory tests pass.
- [x] Runtime-style LLM call smoke passes against Factory.
- [x] Deploy Factory.
- [x] Production smoke: normal chat call logs exactly one selected model path.
- [x] Production log evidence: no `is_fallback` / failover event in recent Factory logs.

## Git / Merge

- [x] Commit in `novaic-llm-factory`.
- [x] Parent repo submodule bump / docs commit.
- [x] Push `main`.
- [x] Mark this ticket `[deployed]` only after deploy evidence is collected.

## Evidence

- Factory tests: `4 passed`.
- Deployed via `./deploy factory`; health returned `{"status":"ok","service":"llm-factory"}`.
- Production smoke `log_id=a10a8ef1-a543-4eb3-b477-20a2d68f39f9` returned:
  - `provider_used=openai`
  - `model_used=kimi-k2.5`
  - `retries=0`
  - `has_is_fallback=false`
