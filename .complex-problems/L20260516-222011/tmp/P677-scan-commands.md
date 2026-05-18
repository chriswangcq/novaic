# P677 deployment script scan commands

```bash
rg --files -g '!.git/**' -g '!.complex-problems/**' -g '!**/__pycache__/**' -g '!**/.pytest_cache/**' -g '!**/*.pyc' \
  | rg '(^|/)(scripts|deploy|deployment|docker|compose|systemd|infra|ops|Procfile|Makefile|justfile|Taskfile)|(^|/)[^/]*(deploy|start|smoke|health|supervis|worker|scheduler|service)[^/]*\.(sh|py|js|ts|mjs|yml|yaml|toml|service)$' \
  | sort > .complex-problems/L20260516-222011/tmp/P677-candidate-files.txt

rg -n -S --hidden -g '!.git/**' -g '!.complex-problems/**' -g '!**/__pycache__/**' -g '!**/.pytest_cache/**' -g '!**/*.pyc' \
  '(deploy|deployment|start|supervis|worker|scheduler|health|smoke|systemd|docker compose|queue-service|task-worker|saga-worker|outbox|logicalfs|sandboxd|blob)' . \
  > .complex-problems/L20260516-222011/tmp/P677-keyword-scan.txt

wc -l .complex-problems/L20260516-222011/tmp/P677-candidate-files.txt .complex-problems/L20260516-222011/tmp/P677-keyword-scan.txt
```
