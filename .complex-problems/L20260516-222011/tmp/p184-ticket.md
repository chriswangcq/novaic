# Audit bounded terminal-style shell projection

## Problem Definition

Shell output must be projected as bounded terminal text, not as raw arbitrary payload or hidden media. P184 verifies the runtime shell wrapper and Cortex projection contract for shell outputs.

## Proposed Solution

Inspect runtime shell wrapper, tool output contract helpers, Cortex step projection, and shell tests. Run focused shell/tool projection tests. Add or fix tests/code if unbounded stdout/stderr can reach LLM text context.

## Acceptance Criteria

- Shell wrapper and projection code are mapped.
- Bounded/truncated public shell output is verified.
- Durable full output remains accessible through step/payload storage.
- Focused shell tests pass.

## Verification Plan

Run `test_shell_output_contract.py`, `test_tool_output_contract.py`, `test_tool_output_projection.py`, and relevant runtime explicit-contract tests.

## Risks

- The shell wrapper and Cortex projection may each truncate at different layers; the audit must distinguish public text from durable payload.

## Assumptions

- This child only covers shell; display/artifacts are separate sibling problems.
