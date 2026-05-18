# Audit UI Monitor and Log Artifact Display Boundary

## Problem Definition

P612 must verify monitor/log display surfaces that can show tool or artifact data do not render raw unbounded image bytes and are distinct from LLM request context.

## Proposed Solution

Run focused scans over Agent Monitor/ActivityTimeline and Factory Logs UI/API surfaces for artifact, raw JSON, request/response, image/base64, and escaping/bounds logic. Reuse P604/P607 evidence where appropriate, but record P612-specific scan/test outputs.

## Acceptance Criteria

- Exact monitor/log scans are recorded.
- Relevant slices cite monitor raw-payload redaction and factory log escaping/bounds/redaction.
- The result clearly separates normal UI presentation from debug/raw views and LLM context.
- A follow-up is created if monitor/log UI surfaces render raw image bytes in normal display paths.

## Verification Plan

Run ActivityTimeline tests and factory log route/chat redaction tests used by P607/P608.

## Risks

- Raw JSON/debug views are intentionally inspectable; judge escaping/bounds rather than requiring all raw inspection to disappear.

## Assumptions

- Factory Logs raw JSON details may show bounded/redacted JSON for debugging, but must not dump image payload bytes unbounded.
