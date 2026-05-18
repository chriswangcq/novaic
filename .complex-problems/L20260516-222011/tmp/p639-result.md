# Cortex RW Scratch Fixture Rewrite Result

## Summary

Closed Cortex root `/rw/scratch` fixture cleanup across workspace/authority, runtime/tool, and path-abuse test categories. Targeted Cortex tests no longer use root `/rw/scratch` as a generic fixture path.

## Done

- P641 rewrote workspace/authority fixtures to neutral `/rw/tmp` and verified 22 tests passed.
- P642 rewrote runtime/tool/metrics/chaos/wave fixtures to neutral `/rw/tmp` and verified 14 tests passed.
- P643 rewrote path normalization/abuse fixtures to neutral `/rw/tmp` and verified 47 tests passed.

## Verification

- P641 check C670 succeeded, citing R629.
- P642 check C671 succeeded, citing R630.
- P643 check C672 succeeded, citing R631.
- Each child recorded a post-change scan showing no root `/rw/scratch` remains in its target files.

## Known Gaps

- Final repository-level `/rw/scratch` scan belongs to P640/P637 guard because lower-layer LogicalFS tests may still intentionally contain generic `/rw/scratch` fixtures.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p641-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p642-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p643-scan.txt`
