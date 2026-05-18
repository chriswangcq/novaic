# P710 Scan Commands

```bash
find novaic-cortex -maxdepth 3 -type f | sort
rg -n "FastAPI|uvicorn|click|argparse|if __name__|def main|app =|serve|router" novaic-cortex -g '*.py'
rg -n "cortex|novaic-cortex|novaic_cortex" . -g '*.sh' -g '*.py' -g '*.ts' -g '*.tsx' -g '*.json' -g '*.toml' -g '*.md' -g 'Dockerfile*' -g 'compose*.yml'
rg -n "logicalfs|LogicalFS|blob|Blob|sandbox|Sandbox|queue|Queue|runtime|Runtime|redis|sqlite|context_stack|scope" novaic-cortex -g '*.py' -g '*.md' -g '*.txt' -g '*.toml'
python3 -m py_compile <selected cortex files>
```
