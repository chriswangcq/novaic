# Shell Observations Terminal-Shaped Check

## Summary

Successful. The shell observation contract is now verified across runtime public output, Cortex projection, and a media-like stdout regression.

## Evidence

- `R047` summarizes closed child problems `P059`, `P060`, and `P061`.
- Runtime shell wrapper bounds public stdout/stderr and stores full raw output only in durable payload.
- Cortex projection uses `llm_content`, not durable `raw.stdout`, for shell history.
- New `/9j/` media-like regression tests prevent shell stdout from becoming display/image content.

## Criteria Map

- Shell result projection has explicit length bounds and terminal-style text semantics:
  - Satisfied by P059 and P061 runtime tests.
- Shell output contract documents complete data lives in Cortex RO/payload records rather than inline context:
  - Satisfied by runtime durable payload behavior and Cortex projection tests.
- Tests/scans cover a large-media stdout case:
  - Satisfied by P061 runtime and Cortex tests using `/9j/`-style stdout.

## Execution Map

- `P059` audited runtime shell bounds.
- `P060` audited Cortex shell projection.
- `P061` added the media-like regression tests.

## Stress Test

- The regression payload matches the observed failure shape: screenshot-like JPEG base64 beginning with `/9j/`.
- Tests assert this text remains bounded terminal output and cannot be projected as an image.

## Residual Risk

- Low. Shell remains capable of printing arbitrary text, including base64-like text, but context receives a bounded terminal preview and explicit payload inspection is required for full data.

## Result IDs

- R047
