# Add Entangled Migration CLI Entry Point And Test Coverage

## Problem

The planner and executor must be exposed through a safe command-line entry point and verified as a complete offline migration command. This belongs under `P049` because operators need one command with clear flags, DSN-file support, failure behavior, and a redacted report before staging validation can run.

## Success Criteria

- A CLI entry point exists under `Entangled/packages/server-python/scripts/` or `[project.scripts]`.
- CLI arguments include SQLite source path, Postgres DSN or DSN file, report output path, explicit clean-target flag, target confirmation, and an optional dry-run/planning mode if implemented.
- DSN file contents are read for connection only and never printed or stored in reports.
- CLI failure messages avoid secret values.
- End-to-end command tests exercise safe failure without clean confirmation and a successful fixture/fake migration path that writes a report.
- `python -m py_compile` passes for new modules/scripts.
- Full Entangled server-python pytest passes.
