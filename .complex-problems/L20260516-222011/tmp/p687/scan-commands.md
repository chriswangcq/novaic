# P687 Python module/CLI entrypoint scan commands

```bash
rg --files -g '*.py' -g 'pyproject.toml' -g 'setup.py' -g 'setup.cfg' \
  -g '!**/.venv/**' -g '!**/venv/**' -g '!**/__pycache__/**' -g '!**/node_modules/**' -g '!**/target/**' -g '!**/.git/**'

rg -n '(if __name__ == .__main__.|uvicorn|gunicorn|argparse|click|typer|console_scripts|\[project\.scripts\]|python -m)' ...

rg -n -i '(queue|agent.?runtime|cortex|sandbox|logicalfs|blob|gateway|business|device|saga|outbox|scheduler|health)' ...
```
