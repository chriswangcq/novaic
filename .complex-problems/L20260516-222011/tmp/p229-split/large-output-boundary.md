# Audit large shell/display output projection boundary

## Problem

Large shell stdout, CLI artifact manifests, and display/image outputs must remain compact in model-visible text. Any raw base64 or large stdout should be behind durable payload or explicit artifact/display handling, not normal history text.

This belongs under `P229` because shell/display were the concrete regression class that previously put huge/base64 data into context.

## Success Criteria

- Shell result projection and display/media result projection paths are mapped with file/function pointers.
- Evidence shows large/base64 output is truncated or replaced with manifest/projection text in normal context.
- Focused tests pass for shell output truncation, artifact manifest handling, display media handling, and no historical tool image/base64 injection.
