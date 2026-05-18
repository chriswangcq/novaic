# Cortex RW Scratch Fixture Rewrite

## Problem

Cortex tests use root `/rw/scratch` as generic writable fixture paths. These tests should use neutral `/rw/tmp` or current subagent-aware scratch paths so root scratch no longer looks canonical.

## Success Criteria

- Rewrites Cortex test fixture paths from `/rw/scratch` to appropriate current paths.
- Preserves each test's original invariant: path normalization, binary IO, truncation, metrics, abuse rejection, and RW tree reading.
- Keeps current `/rw/subagents/main/scratch` sandboxd tests intact.
- Runs focused tests for touched files.
