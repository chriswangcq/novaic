# Child Problem: shell observations stay terminal-shaped

## Problem

The shell tool should behave like a human terminal: return bounded text output and pointers, not structured media blobs. Even when a subprocess emits large JSON or accidental base64, shell observation projection should remain bounded and should not encourage the model to treat truncated binary text as semantic context.

## Success Criteria

- Shell result projection has explicit length bounds and terminal-style text semantics.
- Shell output contract documents that complete data lives in Cortex RO steps/artifacts rather than inline LLM context.
- Tests or scans cover a large-media stdout case and prove context receives only bounded text or manifests.
