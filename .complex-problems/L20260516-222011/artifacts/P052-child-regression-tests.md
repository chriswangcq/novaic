# Child Problem: large media-like shell stdout regression coverage

## Problem

The project needs a regression test that simulates a shell command emitting large media/base64-like stdout and proves the LLM-facing context receives only bounded terminal text. Without this, future shell/CLI changes can accidentally reintroduce base64-as-context behavior.

## Success Criteria

- A focused test simulates large base64-like stdout from shell.
- The test asserts the model-visible shell observation is truncated/bounded and not interpreted as image/display content.
- The test is run together with adjacent shell/context projection tests.
