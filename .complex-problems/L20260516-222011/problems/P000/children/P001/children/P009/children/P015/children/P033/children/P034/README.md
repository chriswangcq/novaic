# Child Problem: policy and API vocabulary classification

## Problem

Policy allowlists and internal API endpoint names legitimately need to know about migrated direct-tool names, but those references should be mechanically isolated from active LLM-facing tool-surface vocabulary.

## Success Criteria

- Classify remaining policy/API direct-tool tokens.
- Keep necessary migration allowlists/endpoints, but name/comment them as migrated, legacy, or shell-capability backing APIs.
- Avoid ordinary docs/comments implying these names are active direct executors.
- Verify with focused grep and relevant tests/py_compile.
