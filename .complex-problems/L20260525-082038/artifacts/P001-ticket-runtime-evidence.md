# Trace recent production message flow

## Problem Definition

The current no-response report needs runtime evidence. We need to identify whether messages are failing before persistence, after persistence but before dispatch, during queue/saga execution, in Cortex/LLM execution, or during reply projection.

## Proposed Solution

Inspect the relevant code entry points, then query production service state and logs around the latest user message. Focus on Business `messages.send`, Entangled persistence, queue-service sagas/tasks, subscriber dispatch, Cortex runtime logs, and Gateway/API health.

## Acceptance Criteria

- Recent message pipeline evidence is collected from production or directly relevant runtime logs.
- The failing stage is named with evidence.
- The next fix target is precise enough to implement.

## Verification Plan

Use read-only code and service inspection first; only perform minimal safe API probes if needed. Record commands and observations in the result.

## Risks

- Message content may be user data; avoid dumping full private message bodies.
- Logs can be noisy after recent deployments.

## Assumptions

- The failure happened in prod after the latest deployment.
- Recent logs still contain the failing request or downstream wake attempt.
