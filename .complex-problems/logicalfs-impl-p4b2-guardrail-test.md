# Implement Blob Boundary Guardrail Test

## Problem

The repository needs an automated guardrail that fails when live Cortex `RO` / `RW` code reintroduces direct Blob object-store authority outside the narrow file authority boundary. The guardrail must be precise enough to permit legitimate Blob byte flows.

This child belongs under T006 because it turns the allowlist into executable protection.

## Success Criteria

- A targeted test or CI-accessible script scans source files for forbidden Blob object-store bypass patterns.
- The scanner uses the allowlist from the previous child problem.
- The scanner is checked into the repo and runs in a targeted test command.
- Current allowed Blob byte flows pass the guardrail.
