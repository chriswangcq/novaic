# Record Queue Postgres Staging Validation Report

## Problem

P076 needs a durable staging evidence artifact that can be reviewed before production cutover. The report must summarize database preparation, service/API smokes, worker/outbox smokes, command outputs, counts, failures, and secret redaction.

## Success Criteria

- A redacted report artifact is created under the ledger artifacts directory.
- Report includes commands run, timestamps, target identity redaction, health checks, API smoke results, worker/outbox smoke results, DB counts, and residual risks.
- Report explicitly states whether P076 is ready for production cutover or blocked.
- No DSNs, passwords, tokens, or secret file paths are present in the report.
