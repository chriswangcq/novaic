# Phase 3A Active Stack Authority Audit

## Problem

Before changing runtime stack authority, identify every active-stack/status read and write path and classify whether it belongs to operational control state, semantic context projection, or trace/debug output. This prevents mixing the SQLite control stack with the existing context event projection stack.

## Success Criteria

- All `_collect_active_stack`, `context_status`, `skill_begin`, `skill_end`, finalize, and stack-projection call sites are cataloged.
- Each call site is classified as runtime authority, semantic context projection, trace/debug, or test-only.
- The next implementation tickets have explicit dependency boundaries and no ambiguous stack source remains unclassified.
