# Python module and CLI entrypoint scan

## Problem

Find Python service/worker entrypoints, `if __name__ == "__main__"` modules, Typer/Click/argparse CLI entrypoints, uvicorn/gunicorn references, and package metadata console scripts relevant to backend workers/services.

## Success Criteria

- Candidate Python entrypoint modules and console-script metadata are scanned and saved with commands.
- Known queue/runtime/Cortex/sandbox/blob/logicalfs surfaces appear or their absence is explained.
- No production code is changed.
