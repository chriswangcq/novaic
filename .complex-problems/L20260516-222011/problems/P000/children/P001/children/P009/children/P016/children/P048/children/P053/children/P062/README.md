# Child Problem: classify active base64 leakage surfaces

## Problem

Before adding a broad guard, the active code paths and legitimate fixtures need classification. Otherwise the guard may either miss the real public-text leak paths or flag legitimate provider-native image payloads.

## Success Criteria

- Active source/test occurrences of `/9j/`, `data:image`, `base64`, display, shell, and image projection are scanned.
- Legitimate structured image payload uses are separated from forbidden public text/log/context leakage.
- The audit identifies exactly where a guard should live.
