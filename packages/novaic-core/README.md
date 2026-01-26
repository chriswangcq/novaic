# NovAIC Core

> The AI Computer Engine - 44+ MCP tools for AI desktop control

NovAIC = Nov(a) + AIC (AI Computer)

## Installation

```bash
pip install novaic
```

## Quick Start

```bash
# Start the MCP server
novaic serve

# Or with uvicorn directly
python -m uvicorn novaic_core.main:app --host 0.0.0.0 --port 8080
```

## Features

- 🖥️ **Desktop Control** - Screenshot, mouse, keyboard
- 🌐 **Browser Automation** - Navigate, click, type, scroll
- 💻 **Shell Execution** - Run commands and Python code
- 📁 **File Operations** - Read, write, list files
- 🪟 **Window Management** - List, focus, launch apps
- 🧠 **Memory System** - Persistent key-value storage
- 👁️ **Context Awareness** - System and directory snapshots
- 📦 **Result Cache** - Handle large outputs gracefully

## MCP Tools (44+)

### Desktop
- `screenshot` - Take a screenshot
- `mouse` - Mouse actions (move, click, drag, scroll)
- `keyboard` - Keyboard input

### Browser
- `browser_navigate` - Navigate to URL
- `browser_click` - Click element
- `browser_type` - Type text
- `browser_screenshot` - Browser screenshot
- `browser_scroll` - Scroll page
- `browser_eval` - Execute JavaScript

### Shell
- `run_command` - Execute shell command
- `run_python` - Execute Python code

### Files
- `read_file` - Read file contents
- `write_file` - Write to file
- `list_files` - List directory
- `file_info` - Get file info

### Windows
- `list_windows` - List all windows
- `focus_window` - Focus a window
- `launch_app` - Launch application
- `maximize_window` - Maximize window
- `close_window` - Close window

### Memory
- `memory_save` - Save to memory
- `memory_recall` - Recall from memory
- `memory_delete` - Delete memory
- `task_log` - Log task
- `task_history` - Get task history
- `goal_set` - Set goal
- `goal_progress` - Update goal progress
- `goal_complete` - Complete goal
- `session_state` - Get session state

### Context
- `system_snapshot` - System overview
- `directory_snapshot` - Directory analysis
- `app_state` - Application state
- `clipboard_get` - Get clipboard
- `clipboard_set` - Set clipboard
- `recent_files` - Recent files
- `environment_info` - Environment info

### Result Cache
- `result_get` - Get cached result
- `result_info` - Result metadata
- `result_list` - List cached results

## Configuration

Environment variables (prefix: `NOVAIC_`):

```bash
NOVAIC_HOST=0.0.0.0
NOVAIC_PORT=8080
```

Config directory: `~/.novaic/`

## License

MIT
