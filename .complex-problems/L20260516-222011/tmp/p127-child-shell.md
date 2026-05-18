# Shell projection bounded terminal text

## Problem

Shell output should look like terminal text to the LLM and monitor, with bounded/truncated public text and no hidden artifact/media payload injection. This contract must be audited at both Cortex projection and runtime shell wrapper boundaries.

## Success Criteria

- Map shell output projection functions and runtime shell wrapper behavior.
- Prove public shell text is bounded/truncated and terminal-style.
- Prove large shell output remains inspectable through durable step/payload refs rather than inline context.
- Fix or split any branch that emits unbounded shell text.
