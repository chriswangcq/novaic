# Process Cache Config And Documentation Residue Cleanup

## Problem

Cortex still has process-local registry caches, startup config, lock backend globals, and some stale comments. These are mostly not durable authority, but they can confuse future maintainers and tests.

## Success Criteria

- Classify which process-local state is allowed cache/config.
- Define explicit dependency boundaries for caches, clocks, ids, env, and service clients.
- Identify documentation/code residue to clean so future agents do not infer wrong architecture.

