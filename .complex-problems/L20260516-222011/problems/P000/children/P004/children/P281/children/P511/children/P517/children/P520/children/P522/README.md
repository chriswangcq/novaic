# Repair Attach Outbox Published Status Failure

## Problem

`test_outbox_records_start_and_published_attach_effects_after_cutover` expects attach outbox effect status `published`, but current behavior leaves it `pending`.

## Success Criteria

- Determine whether attach effects should be auto-published in this test setup or remain pending for worker dispatch.
- Apply minimal correct code/test update.
- Rerun the failing test successfully.
