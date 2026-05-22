# Compile Queue Postgres Staging Validation Report

## Problem Definition

P076 needs one durable, redacted staging validation report before production cutover. Existing artifacts prove separate slices such as database setup, Queue Service health, API smoke, post-smoke counts, and worker/outbox smoke, but the evidence is spread across multiple result files and may include operational paths that should not appear in the final cutover-facing report.

## Proposed Solution

Read the completed Queue Postgres staging artifacts and synthesize a single Markdown validation report under the ledger artifacts directory. Include the commands and timestamps at a safe level, summarize target identity without secrets or DSN paths, map health/API/worker/count evidence, document failures that were found and fixed, and clearly state whether P076 is ready for production cutover or blocked.

## Acceptance Criteria

- A redacted validation report artifact is created under `.complex-problems/L20260522-091929/artifacts/`.
- The report includes staging target summary, commands run, timestamps, Queue Service health, API smoke result, worker/outbox smoke result, DB count deltas, fixed failures, and residual risks.
- The report states a cutover readiness decision for P076.
- The report contains no DSN values, passwords, tokens, or secret file paths.

## Verification Plan

Inspect the report with text searches for known secret/path markers, compare its facts against the API smoke, count, and worker smoke JSON artifacts, and record the report path plus redaction check result in the ticket result.

## Risks

- Source artifacts may include DSN file paths; the synthesized report must paraphrase them as a redacted DSN-file configuration rather than copying those paths.
- A readiness statement could overreach beyond Queue Service staging evidence; limit the decision to P076's Queue Postgres staging validation scope.

## Assumptions

- Existing artifacts from P111/P112/P113/P107 are sufficient to compile the report without rerunning staging smokes.
- Internal hostnames, loopback ports, commit IDs, and non-secret command names are safe to include.
