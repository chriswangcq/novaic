# Implement common sandbox infrastructure modules

## Problem

Create stable, business-agnostic infrastructure modules under `novaic-common/common/sandbox`.

## Success Criteria

- Common process runner module exists with stable spec/result dataclasses.
- Common mount namespace module exists with capability detection and bind command construction.
- Common filesystem utility module exists for path-safe component, root-relative cwd resolution, file snapshots, changed paths, and output path sanitization.
- Common tests cover these APIs.
