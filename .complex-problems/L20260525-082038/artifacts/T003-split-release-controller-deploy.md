# Release Controller deploy

## Problem

Deploy the new source through the centralized Release Controller, not by manually invoking backend service deploy scripts.

## Success Criteria

- Release Controller is healthy and its worktree sees the pushed parent commit.
- A staging release is triggered/executed for the new commit.
- The same release/image is promoted to prod through Release Controller.
- The deployed prod containers run the new immutable image/tag.
