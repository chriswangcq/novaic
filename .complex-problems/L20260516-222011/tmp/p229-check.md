# Check: payload write and normal context assembly boundaries are solved

## Summary

`P229` is solved by `R227` and its four closed child branches. The write path records and preserves `step_ref`/`payload_ref`, event projection keeps compact pointer-bearing observations, runtime LLM context expansion uses `/v1/steps/read_formatted` rather than full payload reads, and combined shell/display regression tests pass.

## Evidence

- `P231`/`R223`/`C237`: active tool write path is durable-payload/ref based across runtime handoff and Cortex workspace persistence.
- `P232`/`R224`/`C238`: event writer/projection preserves pointer metadata and compact observations.
- `P233`/`R225`/`C239`: default LLM context expansion uses formatted step projection and negative runtime search found no default `/v1/payload/read` path.
- `P234`/`R226`/`C240`: combined large shell/display regression tests pass.

## Criteria Map

- Tool/step write path records `step_ref`/`payload_ref` evidence: satisfied by `P231` and its child checks.
- Normal LLM context expansion path does not call full payload read by default: satisfied by `P233` code/search/test evidence.
- Large shell/display raw data stays behind durable payload or explicit payload APIs: satisfied by `P231`, `P234`, and supporting shell/display tests.

## Execution Map

- Split ticket `T222` created `P231`, `P232`, `P233`, and `P234`.
- Each child problem has a recorded result and success check.
- Parent result `R227` summarizes the closed child evidence.

## Stress Test

The deepest plausible failure chain is: shell/display writes heavy data, event projection expands it, runtime context reads full payload, then LLM request receives raw/base64 text. The child audits cover every link in that chain and the final combined tests cover large shell + display regressions together.

## Residual Risk

Non-blocking for `P229`: explicit payload CLI/tool exposure and docs/schema guidance remain open under sibling `P230`.

## Result IDs

- `R227`
- `R223`
- `R224`
- `R225`
- `R226`
