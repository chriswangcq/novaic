# Runtime Local Shell Fallback Residue Audit

## Problem

The runtime should use the intended LogicalFS/sandbox service path, not silently fall back to local shell execution or local filesystem materialization when service wiring is unavailable.

## Success Criteria

- Scans runtime/cortex/sandbox code for local shell fallback, direct subprocess/local execution fallback, `fallback`, `local`, and sandbox service bypass terms.
- Classifies remaining hits as intended error handling/test coverage or active hidden fallback.
- Removes or creates follow-up for any active hidden fallback that can run instead of failing loudly.
