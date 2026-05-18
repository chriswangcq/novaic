# Child Problem: Factory logs safe projection helper

## Problem

`factory-logs.html` needs a reusable client-side helper that summarizes unsafe values consistently instead of each renderer inventing its own truncation behavior.

## Success Criteria

- A local helper detects and summarizes long strings, base64-like strings, large arrays, large objects, and known payload-ish keys.
- The helper keeps compact values and BlobRefs readable.
- The helper output is deterministic and simple enough to test without a frontend build.
