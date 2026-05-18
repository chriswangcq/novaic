# PR-62 — LLM request builder should not send null optional generation parameters

| Field | Value |
|---|---|
| **Ticket** | PR-62 |
| **Status** | `[✓]` 2026-04-25 — implemented, tested, deployed |
| **Opened** | 2026-04-25 |
| **Owner** | __ |
| **Severity** | P2 provider compatibility — optional params sent as JSON null can be rejected or interpreted differently across providers. |
| **Blocks** | Stable model-provider abstraction and reproducible LLM call snapshots. |
| **Blocked by** | — |
| **Invariant** | Optional LLM request parameters should be omitted when unset, not serialized as `null`, unless the provider explicitly requires null. |

## Bug

The latest LLM request includes:

```json
"temperature": null
```

For optional generation parameters, `null` is not equivalent to omission across all OpenAI-compatible providers.

## Evidence

Source: user-provided LLM request snapshot on 2026-04-25 15:37 Asia/Shanghai.

The payload includes `max_tokens: 4096` and `temperature: null`.

## Impact

- Provider adapters may fail with validation errors.
- Two providers can interpret the same request differently.
- Snapshot comparisons become noisy because unset fields are serialized.

## Acceptance Criteria

- LLM request snapshots omit unset optional parameters.
- Provider-specific defaults remain controlled by the model/provider layer.
- A regression test covers `temperature=None` or equivalent unset input.

## Out of Scope

This ticket intentionally does not specify a repair method.
