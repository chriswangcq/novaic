# Sandboxd independent service

## Problem

Sandbox process execution currently lives in the Cortex process. It should become an independent base service that owns process spawning and mount namespace command wrapping while remaining business-agnostic.

## Success Criteria

- A new `novaic-sandbox-service` package exposes health and execute endpoints.
- The execute endpoint accepts the common sandboxd contract and runs through common sandbox process primitives.
- The service has no Cortex workspace/blob/agent imports.
- Service tests verify successful execution, mount-plan execution path shape, timeout behavior, and error handling.
