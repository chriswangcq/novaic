# Retained ServiceConfig boundary classification ticket

## Problem Definition

After removing direct react saga decision config reads, remaining `ServiceConfig` references in runtime queue/task code must be classified. The goal is to separate valid adapter/process-boundary configuration from risky hidden inputs in business decisions.

## Proposed Solution

Run a focused `ServiceConfig` inventory over runtime queue/task code, save the artifact, inspect each retained category, and classify hits as process startup, client adapter, tool adapter, retry policy adapter, saga provider boundary, or risky decision-path hidden input. Do not edit source unless a risky hit is small and obviously in scope; otherwise route it to a follow-up.

## Acceptance Criteria

- Saved classification artifact covers every current `ServiceConfig` hit in `queue_service` and `task_queue`.
- React saga decision adapters are confirmed clean after P472.
- Retained hits are classified by boundary type.
- Any risky decision-path hidden input is explicitly called out for follow-up rather than waived.

## Verification Plan

Use `rg` artifacts plus representative source slices. Run the react saga source guard from P477 and focused tests if classification touches code.

## Risks

- Over-classifying adapter reads as risky could create unnecessary plumbing.
- Under-classifying decision reads could leave hidden behavior.

## Assumptions

- This is primarily classification; P469 parent can still close only if risky hits are handled or routed.
