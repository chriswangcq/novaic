# LogicalFS layering and module boundary cleanup

## Problem

The current Cortex shell path works, but the physical code layout is confusing: `novaic_cortex/sandbox.py` contains capability CLI generation, stable `/cortex` path handling, LogicalFS materialization/flushing, mount namespace command wrapping, process execution, and the public `Sandbox` facade in one large file.

The user suspects the intended layering should read as Cortex at the top, Sandbox below it, Blob near the bottom, and LogicalFS as the final filesystem layer. We need to systemically audit that mental model, settle the canonical dependency direction, and refactor modules if the current physical layout would mislead future work.

This must follow AI-era cleanup principles: avoid half-migrations, avoid stale alternate paths, avoid local fallback, make boundaries explicit, and leave one clear current path.

## Success Criteria

- Current active shell/logical filesystem path is audited against the intended Cortex/Sandbox/LogicalFS/Blob responsibilities.
- The final layering is documented in plain terms, including call flow and dependency flow.
- If module extraction is necessary, the code is physically split so the module names match the architectural layers.
- No local fallback or compatibility branch is reintroduced.
- Active imports/tests are updated to use the new boundaries, with any necessary re-exports kept only when they do not create misleading current paths.
- Verification covers unit tests for sandbox/logicalfs/tool output behavior and a residue scan for old fallback or confusing path rewrite logic.
