# Analyze Device screenshot route usage

## Summary

Inspect the Device VmControl screenshot route, route mounting, tests, and in-repo callers to recommend a safe disposition.

## Problem Definition

The route may be legacy/debug-only, but it is mounted and returns inline MCP image content. Caller analysis is required before modifying it.

## Proposed Solution

Use targeted searches and code inspection to identify implementation, mount points, tests, and callers. Record a disposition recommendation for the implementation child.

## Acceptance Criteria

- Route implementation and mount are identified.
- In-repo callers are found or absence is demonstrated.
- Existing tests are identified.
- Recommendation is clear enough for implementation: remove, mark legacy/debug-only, convert, or spawn external-compatibility blocker.

## Verification Plan

- Run `rg` across repo for the route path, handler names, and screenshot client methods.
- Inspect `novaic-device` route mounting and tests.
- Produce a result with exact file pointers.
