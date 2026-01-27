# NovAIC Core

> MCP Tool Server — 44+ tools for AI desktop control

[![PyPI](https://img.shields.io/pypi/v/novaic-core.svg)](https://pypi.org/project/novaic-core/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

NovAIC Core is the MCP (Model Context Protocol) server that provides AI agents with tools to control a Linux desktop environment. It includes 44+ tools for:

- Desktop control (screenshot, mouse, keyboard)
- Browser automation (navigate, click, type, scroll)
- Shell execution (commands, Python code)
- File operations (read, write, list)
- Window management (list, focus, launch)
- Memory system (persistent key-value storage)
- Context awareness (system snapshots, directory analysis)

## Installation

```bash
pip install novaic-core
```

Or install from source:

```bash
cd novaic-core
pip install -e .
```

## Quick Start

```bash
# Start the MCP server
novaic serve

# Or with uvicorn directly
python -m uvicorn novaic_core.main:app --host 0.0.0.0 --port 8080
```

## Configuration

Environment variables (prefix: `NOVAIC_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `NOVAIC_HOST` | `0.0.0.0` | Server host |
| `NOVAIC_PORT` | `8080` | Server port |
| `NOVAIC_DEBUG` | `false` | Debug mode |

Config directory: `~/.novaic/`

## MCP Tools Reference

### Desktop Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `screenshot` | Take a screenshot | `region?`, `show_grid?` |
| `mouse` | Mouse actions | `action`, `x?`, `y?`, `button?` |
| `keyboard` | Keyboard input | `action`, `text?`, `keys?` |

**Mouse actions:** `move`, `click`, `double_click`, `right_click`, `drag`, `scroll`

**Keyboard actions:** `type`, `press`, `hotkey`

### Browser Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `browser_navigate` | Navigate to URL | `url` |
| `browser_click` | Click element | `selector` |
| `browser_type` | Type into element | `selector`, `text` |
| `browser_screenshot` | Browser screenshot | — |
| `browser_scroll` | Scroll page | `direction`, `amount?` |
| `browser_eval` | Execute JavaScript | `script` |
| `browser_get_text` | Get element text | `selector` |
| `browser_wait` | Wait for element | `selector`, `timeout?` |

### Shell Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `run_command` | Execute shell command | `command`, `timeout?` |
| `run_python` | Execute Python code | `code` |

### File Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `read_file` | Read file contents | `path`, `encoding?` |
| `write_file` | Write to file | `path`, `content` |
| `list_files` | List directory | `path`, `recursive?` |
| `file_info` | Get file metadata | `path` |
| `delete_file` | Delete file | `path` |
| `copy_file` | Copy file | `src`, `dest` |
| `move_file` | Move file | `src`, `dest` |

### Window Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_windows` | List all windows | — |
| `focus_window` | Focus a window | `window_id` or `title` |
| `launch_app` | Launch application | `app_name` |
| `maximize_window` | Maximize window | `window_id` |
| `minimize_window` | Minimize window | `window_id` |
| `close_window` | Close window | `window_id` |

### Memory Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `memory_save` | Save to memory | `key`, `value` |
| `memory_recall` | Recall from memory | `key` |
| `memory_delete` | Delete from memory | `key` |
| `memory_list` | List all keys | — |
| `task_log` | Log a task | `task`, `status` |
| `task_history` | Get task history | `limit?` |
| `goal_set` | Set a goal | `goal`, `steps?` |
| `goal_progress` | Update goal progress | `progress`, `notes?` |
| `goal_complete` | Complete goal | `result?` |
| `session_state` | Get session state | — |

### Context Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `system_snapshot` | System overview | — |
| `directory_snapshot` | Analyze directory | `path` |
| `app_state` | Application state | `app_name?` |
| `clipboard_get` | Get clipboard | — |
| `clipboard_set` | Set clipboard | `content` |
| `recent_files` | Recent files | `limit?` |
| `environment_info` | Environment info | — |

### Result Cache Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `result_get` | Get cached result | `result_id`, `offset?`, `limit?` |
| `result_info` | Result metadata | `result_id` |
| `result_list` | List cached results | — |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/tools` | GET | List available tools |
| `/call` | POST | Call a tool |
| `/sse` | GET | Server-Sent Events (MCP protocol) |

## Example Usage

### Screenshot with Grid

```python
import httpx

response = httpx.post("http://localhost:8080/call", json={
    "tool": "screenshot",
    "arguments": {"show_grid": True}
})
result = response.json()
# Returns base64 encoded image
```

### Run Python Code

```python
response = httpx.post("http://localhost:8080/call", json={
    "tool": "run_python",
    "arguments": {
        "code": """
import pandas as pd
df = pd.read_csv('data.csv')
print(df.describe())
"""
    }
})
```

### Save and Recall Memory

```python
# Save
httpx.post("http://localhost:8080/call", json={
    "tool": "memory_save",
    "arguments": {
        "key": "project_context",
        "value": {"name": "My Project", "status": "in_progress"}
    }
})

# Recall
response = httpx.post("http://localhost:8080/call", json={
    "tool": "memory_recall",
    "arguments": {"key": "project_context"}
})
```

## Project Structure

```
novaic-core/
├── src/novaic_core/
│   ├── __init__.py
│   ├── main.py           # MCP Server entry point
│   ├── cli.py            # CLI commands
│   ├── config.py         # Configuration
│   └── tools/
│       ├── __init__.py
│       ├── desktop.py    # screenshot, mouse, keyboard
│       ├── browser.py    # browser automation
│       ├── shell.py      # run_command, run_python
│       ├── files.py      # file operations
│       ├── windows.py    # window management
│       ├── memory.py     # memory system
│       ├── context.py    # context awareness
│       └── result_cache.py # result caching
├── skills/               # Skill documentation
├── tests/
├── pyproject.toml
└── README.md
```

## Skills Documentation

Each tool category has detailed skill documentation in the `skills/` directory:

- [Desktop Skills](skills/desktop/SKILL.md) — Screenshot, mouse, keyboard guidance
- [Browser Skills](skills/browser/SKILL.md) — Browser automation best practices
- [Shell Skills](skills/shell/SKILL.md) — Command execution guidelines
- [Files Skills](skills/files/SKILL.md) — File operation patterns
- [Windows Skills](skills/windows/SKILL.md) — Window management
- [Memory Skills](skills/memory/SKILL.md) — Memory system usage
- [Context Skills](skills/context/SKILL.md) — Context awareness
- [Software Skills](skills/software/SKILL.md) — Installing and troubleshooting software

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
isort src/

# Type check
mypy src/
```

## License

MIT
