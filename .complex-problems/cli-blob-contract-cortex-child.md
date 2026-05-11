# Audit and fix cortex CLI Blob contract

## Problem

`cortex payload` shell capability commands inspect Cortex payload refs. They must remain bounded text-inspection tools and must not become unbounded binary or Blob-sized stdout channels.

## Success Criteria

- `cortex payload read` has explicit bounded read modes and size limits.
- `cortex payload search` returns bounded match contexts.
- `cortex payload summarize` and `cortex payload qa` return model-produced text summaries/answers, not raw payload bytes.
- Any unbounded or artifact-like stdout behavior is fixed and verified.
- Evidence references concrete code paths and test results.
