# P043 Check

## Judgment

Success.

## Evidence Reviewed

- Result `R025`.
- Focused test run.
- Focused `im_read` / `im_reply` scan of `test_pr193_activity_projection.py`.

## Stress Check

The old current-path direct `im_read` fixture is gone. The test now models the current path as a shell call to `agentctl im read` with an explicit monitor description, while preserving deterministic projection behavior.

## Residual Risk

Production activity projection legacy label handling remains in `P036`.
