# Contributing

Thanks for your interest in contributing to **NovAIC**.

## Development setup

See [DEVELOPMENT.md](DEVELOPMENT.md).

## Pull requests

- Keep PRs focused and small.
- Add/update docs when behavior changes.
- Run checks locally:
  - `cd app && npm run build`
  - `cd app/src-tauri && cargo check`
  - `cd agent && python -m py_compile main.py` (Agent runs in VM in full mode; this is just a syntax check)
  - `cd cloud && python -m py_compile main.py`

## Reporting bugs

Please include:

- OS + version
- Steps to reproduce
- Expected vs actual behavior
- Logs / screenshots (redact secrets)


