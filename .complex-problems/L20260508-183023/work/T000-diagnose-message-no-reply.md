# Trace latest user message no-reply failure

## Problem Definition

The user sent an IM message to the agent but received no reply and saw no monitor reaction. We need a concrete production diagnosis, not a design-level hypothesis.

## Proposed Solution

Perform a read-only production trace across the message delivery chain:

- identify the latest relevant user IM/event in production storage or logs;
- verify whether it was persisted by Environment/Entangled;
- verify whether subscriber observed or published it;
- verify whether queue/session/FSM received it and decided to attach, start, or recover;
- verify whether runtime workers consumed any resulting work;
- verify whether LLM/reply/outbox produced or failed to produce a response.

The result should name the first broken or missing handoff and the minimal fix direction if the cause is code or config.

## Acceptance Criteria

- Latest relevant user message/event is identified or proven absent from the inspected production data.
- Each stage in the expected path is checked with concrete evidence.
- First broken handoff is stated with timestamps/log lines/DB rows/process state.
- Diagnosis distinguishes deployment/process failure from application logic failure.
- Minimal fix direction is recorded if the cause is actionable.

## Verification Plan

- Inspect production process roster and recent log freshness.
- Inspect production DB schemas and recent rows without mutating data.
- Search logs for user id, agent id, message ids, notification ids, subscriber/session/runtime errors.
- Cross-check DB row timestamps against service logs to avoid false positives from stale logs.

## Risks

- Production schemas may differ from expectation; use schema introspection before queries.
- Message text may contain private data; summarize rather than paste full content.
- The reported message may be outside available retention or in a different environment.

## Assumptions

- Production host is still `root@api.gradievo.com` as used by the deploy/runbook.
- The relevant runtime data lives under `/opt/novaic/data` on the production host.
- Read-only diagnostics are permitted for this incident.
