# Check P746 Against R729

## Summary

`R729` satisfies `P746`. The ambiguous Device Service screenshot route was removed, typed CloudBridge screenshot code was preserved, and focused checks passed.

## Criteria Review

- Device Service route no longer exposes `@router.post("/vms/{vm_id}/screenshot")`: satisfied.
- Typed CloudBridge screenshot code remains untouched: satisfied; `pc_client.vm_screenshot` and `cloud_bridge.rs` remain.
- Focused import/route checks pass: satisfied.
- Targeted search confirms removed handler is gone: satisfied.

## Stress Review

The first path assertion failure was due to a test assertion mistake, not product behavior. The corrected prefixed route-path assertion proved the route is absent while neighboring routes still mount.

## Residual Risk

External clients are not discoverable from repo. This is acceptable under the current no-backward-compat cleanup principle and P745's caller analysis.

## Verdict

Success.
