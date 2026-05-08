# T006 Handler Registry Metadata And Boundary Guard

## Problem Definition

Task handler registration only stores topic-to-function mappings. That preserves runtime behavior, but it does not expose declarative metadata such as pool, module, and handler name, so boundary checks cannot distinguish business computation from worker lifecycle/runtime ownership.

## Proposed Solution

- Add a `HandlerSpec` metadata record in `task_queue.handlers`.
- Populate handler metadata at registration time without changing existing handler decorators.
- Add query helpers for handler specs.
- Add tests proving:
  - handler metadata includes topic, pool, module, and handler name
  - existing handler lookup and pool topic behavior remains compatible
  - handler modules do not import worker lifecycle/runtime ownership or queue DB surfaces

## Verification Plan

- Run new handler metadata/boundary tests.
- Run existing handler lookup/topic tests if present.
- Run runtime supervision lint.

## Acceptance Criteria

- Handler registration exposes declarative metadata.
- Existing `get_handler`, `get_all_topics`, and pool lookup behavior remains compatible.
- Handler modules remain free of worker lifecycle/process/runtime ownership imports.
