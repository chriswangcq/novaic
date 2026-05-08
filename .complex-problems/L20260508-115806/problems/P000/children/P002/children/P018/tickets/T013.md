# Generic Worker Assembly Helper Substrate

## Problem Definition

Worker assembly code repeats the same component-level lifecycle wiring in every worker function. Before shrinking business assemblies, we need a small generic helper substrate that can build standard worker lifecycle shapes without importing business-specific modules.

## Proposed Solution

Add `task_queue/workers/assembly_helpers.py` with helpers for:

- standard worker log formatting
- creating runtime bundles with explicit worker dependencies and worker id
- creating `WorkerRuntime`
- building generic, concurrent, and synthetic generic workers
- building synthetic drain/tick workers with custom runtime/reporters

Keep the helper module business-agnostic and focused on component lifecycle only.

## Acceptance Criteria

- Helper module builds generic workers, concurrent workers, and synthetic workers.
- Helper module does not import task/saga/session business modules.
- Helpers keep source, handler, reporter, runtime deps, and cleanup explicit.
- Tests or compile checks verify the helper substrate.

## Verification Plan

- Add focused helper tests.
- Compile helper module.

## Risks

- Helpers that know business worker names or clients would recreate the same coupling; tests should guard against business imports.

## Assumptions

- `queue_service.worker` is the generic worker substrate and is allowed here.
