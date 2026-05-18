# Cortex API step projection boundary audit

## Problem

The Cortex API endpoint that records tool steps must normalize and write structured observations through `write_step_projection`, and tests must prove request data becomes a stored step plus index metadata without inline raw results.

This belongs under `P148` because it is the primary active Cortex write path for tool-step projections.

## Success Criteria

- API request model and handler for step writes are mapped with source pointers.
- The handler calls `normalize_step` and `write_step_projection` or an equivalent strict boundary.
- Tests prove unsafe inline `result` is rejected through the API path.
- Tests prove a valid API request writes a step file and index row with refs/metadata.
