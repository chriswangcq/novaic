# Attach outbox worker-only design

## Problem

Design how to remove repository eager attach publish while keeping attach dispatch durable and observable.

## Success Criteria

- Define dispatch result shape after cutover.
- Define whether `publish_attach_input_effect` should be deleted.
- Define test updates and source guards.
