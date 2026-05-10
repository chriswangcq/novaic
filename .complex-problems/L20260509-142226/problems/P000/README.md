# Slow execution backend analysis

## Problem

User reports execution is slow after deploying and testing Host Desktop device tools. Need inspect backend evidence instead of guessing, determine where latency is introduced, and explain root cause or likely bottleneck with concrete pointers.

## Success Criteria

- Identify whether recent slowness is in queue scheduling, Runtime worker execution, LLM/Cortex context preparation, Device proxy/PC client, or logging/IO.
- Use backend evidence from production status, task DB/logs, or remote smoke timing.
- Avoid scanning huge logs naively; use bounded queries and narrow time windows.
- Record evidence and residual uncertainty in a solve-complex-problems ledger.
