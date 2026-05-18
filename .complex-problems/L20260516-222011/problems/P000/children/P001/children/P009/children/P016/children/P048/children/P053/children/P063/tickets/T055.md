# Ticket: implement public-surface base64 leakage guard

## Problem Definition

The audit identified the correct boundary: base64 may exist in structured image/provider fields and durable raw payloads, but must not leak through public text/log/history surfaces. A regression guard should pin this boundary using representative active code paths.

## Proposed Solution

Strengthen focused tests so the same sentinel image/base64 payload is proven absent from public runtime display output, shell public text beyond bounded preview semantics, Cortex historical shell projection, and LLM Factory logs.

## Acceptance Criteria

- Guard coverage exists in active focused test suites rather than only manual scans.
- Guard coverage allows provider-native structured image fields while rejecting public text/log/history leakage.
- Focused runtime, Cortex, and LLM Factory tests pass.

## Verification Plan

Run focused runtime shell/display tests, Cortex projection tests, and LLM Factory chat-route redaction tests.

## Risks

- A single monorepo cross-package test would be brittle. Prefer package-local focused guards tied to each public boundary.

## Assumptions

- Tests added in P061 count as part of the guard if they are package-local, active, and verified here.
