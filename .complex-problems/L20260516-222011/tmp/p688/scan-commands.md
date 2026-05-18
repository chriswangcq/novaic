# P688 config/deploy launch reference scan commands

```bash
rg --files -g '*.yml' -g '*.yaml' -g '*.toml' -g '*.json' -g '*.service' -g '*.plist' -g '*.env' -g 'Dockerfile*' -g 'docker-compose*' -g 'compose*' -g 'Procfile' \
  -g '!**/node_modules/**' -g '!**/target/**' -g '!**/.git/**' -g '!**/.complex-problems/**' -g '!**/package-lock.json' -g '!**/pnpm-lock.yaml'

while read -r file; do rg -n -i '(execstart|command|entrypoint|deploy|service|worker|queue|saga|outbox|scheduler|health|blob|logicalfs|sandbox|cortex|gateway|business|device|agent.?runtime)' "$file"; done < candidate-files.txt
```
