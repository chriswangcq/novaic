# Child Problem: implement active base64 leakage regression guard

## Problem

The repo needs an automated guard in a focused test suite that fails if active shell/display/media/context paths reintroduce raw image base64 in public text or logs.

## Success Criteria

- A guard test is added or existing guard coverage is strengthened using the audit classification.
- The guard permits legitimate structured provider/image fields while rejecting public-text leakage patterns.
- The guard runs with adjacent focused tests and passes.
