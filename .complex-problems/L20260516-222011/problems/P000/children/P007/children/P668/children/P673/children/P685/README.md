# Entrypoint topology docs and guard alignment

## Problem

Compare the discovered worker/service topology against docs, runbooks, CI guards, and launcher wording. Fix low-risk stale explanations or add focused guards where code would otherwise drift back to misleading worker/service topology claims.

## Success Criteria

- Existing docs/runbooks/guards that describe worker or service topology are located and compared against scan/classification results.
- Low-risk stale docs or guard gaps are patched.
- Any intentionally deferred docs/deploy/runtime surfaces are recorded as residual risk.
- Relevant docs lint, guard, syntax, or focused tests pass for changed files.
