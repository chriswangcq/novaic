# Ticket: add active-path base64 leakage guards

## Problem Definition

Several slices now prevent base64 leakage in specific paths, but the repo also needs broad regression guards for active shell/display/media/context code so future changes do not reintroduce raw image base64 in public tool text or LLM request context.

## Proposed Solution

Audit existing guard tests and active paths for base64 leakage coverage. Add a focused guard test if current coverage only tests individual paths and does not scan/classify active source fixtures.

## Acceptance Criteria

- Guard coverage catches obvious image-base64 leakage patterns in active media/display/shell/context output paths.
- Legitimate fixtures or provider-native structured fields are explicitly classified so the guard is not noisy.
- Guard runs as part of an existing focused test suite.

## Verification Plan

Run targeted `rg` scans for `/9j/`, `data:image`, `base64`, `image_url`, display, shell, and tool-output paths. Run focused tests covering the guard and adjacent output contracts.

## Risks

- Overly broad regex guards can block legitimate provider-native structured image payloads or intentional tiny fixtures. The guard must focus on active public-text/context leakage, not all base64 strings.

## Assumptions

- Provider-native image source data may contain base64 in structured fields; this ticket guards text/history/log leakage.
