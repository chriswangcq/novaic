# Release-controller core unit tests

## Problem

Add focused unit tests for the release-controller core so the first implementation has executable proof for the rules that matter most.

This belongs under P002 because core behavior must be testable before Docker packaging, CI guard wiring, and host deployment build on top of it.

## Success Criteria

- Tests cover branch mapping for main, release, and preview branch rules.
- Tests cover immutable image ref acceptance and rejection.
- Tests cover state persistence across store reload.
- Tests cover current and previous pointer updates on successful namespace release.
- Tests cover dry-run command planning without executing host Docker or deploy commands.
- Tests cover API endpoint behavior when the local dependency set supports in-process API testing.
