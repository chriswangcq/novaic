#!/usr/bin/env bash
# Guard App-facing copy against phantom LLM tool examples.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PATTERN='web_search|web_fetch|terminal_bash_exec|auto_notebook_magic|notebook_write|note_db_write|web_crawl_headless|url_extract|os_terminal_exec|bash_cat|mouse_move|python_exec|bash_terminal|bash_cli|web_crawler'

if rg -n "$PATTERN" \
  novaic-app/src/locales \
  novaic-app/update_trans5.py; then
  echo "Phantom tool placeholder found in App-facing i18n copy." >&2
  exit 1
fi

echo "FRONTEND_PHANTOM_TOOLS_LINT=PASS"
