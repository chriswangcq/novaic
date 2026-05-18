# P686 script/package entrypoint scan commands

```bash
rg --files -g '*.sh' -g 'package.json' -g '*.plist' -g '*.service' -g '*.desktop' \
  -g '!**/node_modules/**' -g '!**/target/**' -g '!**/.git/**' | sort

while read -r file; do
  case "$file" in
    *package.json) jq -r 'select(.scripts) | .scripts | to_entries[] | "\(.key): \(.value)"' "$file" ;;
  esac
done < candidate-files.txt

rg -n -i '(start|stop|restart|deploy|smoke|health|worker|service|uvicorn|gunicorn|python -m|agent-runtime|queue-service|sandbox|logicalfs|blob|cortex)' \
  -g '*.sh' -g 'package.json' -g '*.plist' -g '*.service' -g '*.desktop' \
  -g '!**/node_modules/**' -g '!**/target/**' -g '!**/.git/**'
```
