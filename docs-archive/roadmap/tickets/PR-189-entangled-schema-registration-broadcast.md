# PR-189 — Entangled Schema Registration Broadcast

Status: `[closed]` — 2026-05-03

## Goal

Fix App white-screen startup caused by the frontend waiting for a non-empty Entangled schema that never arrives after a startup race.

## Current-State Analysis

The App initializes through:

```text
AgentService.initialize
  -> loadEntangledSubscriptionSchema
  -> entangled_wait_schema(timeoutMs=15000)
```

The Tauri side only resolves this wait after the direct Entangled WS receives a non-empty `schema` frame.

Production logs showed this race:

```text
10:55:54 Entangled started with 0 entities
10:55:57 App direct Entangled WS client connected
10:55:59 Business registered schemas
10:56:00 Device registered schemas
```

Before this fix, Entangled pushed schema only on WS connect. If the App connected before Business/Device schema registration, it received an empty schema frame and no later replacement. The App then timed out with:

```text
Entangled schema not registered after 15000ms
```

## Implementation

- [x] Broadcast a fresh `schema` push to all connected Entangled WS clients after `/v1/schema/register` successfully registers one or more entities.
- [x] Preserve the existing direct Entangled WS schema source of truth.
- [x] Do not add REST schema fallback.
- [x] Keep Gateway as endpoint discovery only.

## Validation

```bash
cd Entangled/packages/server-python
python3 -m pytest -q tests/test_schema_and_notifier.py
python3 -m pytest -q
./deploy entangled
```

Production smoke:

```text
schema#1 entities=20
schema#2 entities=20
SCHEMA_BROADCAST_SMOKE=PASS
```

## Closure

Closed 2026-05-03. Existing clients connected before schema registration now receive the later non-empty schema push; new clients continue to receive schema on connect.
