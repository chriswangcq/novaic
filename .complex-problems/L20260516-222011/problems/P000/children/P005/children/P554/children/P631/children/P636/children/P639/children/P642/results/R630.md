# Runtime and Tool RW Fixture Rewrite Result

## Summary

Rewrote runtime/tool/metrics/chaos/wave generic fixture paths from root `/rw/scratch` to neutral `/rw/tmp`. No root scratch usage remains in the targeted files, and focused tests pass.

## Changes

- `tests/test_runtime.py`: preloaded store key and read path now use `/rw/tmp/big.txt`.
- `tests/test_cortex_chaos.py`: chaos write/read path now uses `/rw/tmp/{sid}/chunk.txt`.
- `tests/test_hooks_limits.py`: hook probe path now uses `/rw/tmp/mono_probe.txt`.
- `tests/test_tool_metrics.py`: metrics probe path now uses `/rw/tmp/metrics_probe.txt`.
- `tests/test_wave4_metrics.py`: wave4 probe path now uses `/rw/tmp/wave4.txt`.

## Verification

- `.complex-problems/L20260516-222011/tmp/p642-scan.txt` shows no `/rw/scratch` remains in targeted files.
- `.complex-problems/L20260516-222011/tmp/p642-tests.txt` shows 14 focused tests passed.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p642-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p642-tests.txt`
