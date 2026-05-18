# Child Problem: SmartValue unused raw renderer cleanup

## Problem

`novaic-app/src/components/Visual/SmartValue.tsx` appears to be a generic value renderer with `JSON.stringify` fallback behavior. If it is unused, keeping it as a dormant raw JSON display component creates misleading residue and future copy/paste risk.

## Success Criteria

- All imports/usages of `SmartValue` are audited.
- If unused, `SmartValue.tsx` is physically deleted.
- If still used, the live usage is narrowed so it cannot blindly render large JSON/base64-like values.
- Focused TypeScript/test checks for affected imports pass.
