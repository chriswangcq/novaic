# P695 scan commands

- `rg --files` with repository noise exclusions to build `all-files.txt`.
- File-path candidate filter for Blob, LogicalFS, Sandbox/Sandboxd, Cortex, Gateway, Business, Device, devicectl, agentctl.
- Text launch/reference scan for service names, start scripts, package scripts, uvicorn/FastAPI/CLI entrypoint idioms, service configs, and port variables.
- Package script extraction from all `package.json` files.
- Per-service matrix generation from candidate path and launch-reference files.
