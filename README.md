<p align="center">
  <img src="packages/novaic-app/public/icon.svg" width="120" alt="NovAIC Logo">
</p>

<h1 align="center">NovAIC</h1>

<p align="center">
  <strong>The AI Computer — A persistent, visual desktop environment for AI agents</strong>
</p>

<p align="center">
  <em>PC is for humans. AIC is for AI. NovAIC is your AI's dedicated computer.</em>
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+"></a>
  <a href="https://nodejs.org/"><img src="https://img.shields.io/badge/node-20+-green.svg" alt="Node.js 20+"></a>
  <a href="https://www.rust-lang.org/"><img src="https://img.shields.io/badge/rust-1.70+-orange.svg" alt="Rust 1.70+"></a>
</p>

---

## What is NovAIC?

NovAIC provides AI agents with a **persistent, visual desktop environment** — a complete Linux VM with 44+ MCP tools for desktop control, browser automation, file operations, and more.

Unlike temporary sandboxes that reset after each session, NovAIC maintains state across sessions. Your AI remembers context, keeps files, and continues work exactly where it left off.

### Key Features

| Feature | Description |
|---------|-------------|
| **Full Desktop Control** | 44+ MCP tools for mouse, keyboard, screenshots, window management |
| **Browser Automation** | Navigate, click, type, scroll — AI controls the browser like a human |
| **Persistent Environment** | QCOW2 disk images preserve everything between sessions |
| **Memory System** | Key-value storage + goal tracking for cross-session context |
| **Context Awareness** | System snapshots, directory analysis, app state detection |
| **Privacy First** | Runs locally in QEMU VM — your data never leaves your machine |
| **Open Source** | MIT license, fully customizable, works with any LLM |

## Quick Start

### Option 1: MCP Server (Recommended)

```bash
# 1. One-command VM setup
cd packages/novaic-vm
./setup.sh

# 2. Configure your MCP client (e.g., Claude Desktop)
# ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "novaic": {
      "url": "http://localhost:8081/sse"
    }
  }
}
```

### Option 2: Python Package

```bash
pip install novaic-core
novaic serve
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         NovAIC Platform                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │  NovAIC App    │  │ Claude Desktop │  │  Any MCP Host  │         │
│  │  (Tauri)       │  │     / CLI      │  │                │         │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘         │
│          │                   │                   │                   │
│          └───────────────────┼───────────────────┘                   │
│                              │ MCP Protocol                          │
│                              ▼                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                       NovAIC Core                              │  │
│  │                  MCP Server (44+ Tools)                        │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │  │
│  │  │ Desktop │ │ Browser │ │  Shell  │ │  Files  │ │ Windows │  │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐                          │  │
│  │  │ Memory  │ │ Context │ │  Cache  │                          │  │
│  │  └─────────┘ └─────────┘ └─────────┘                          │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│                              ▼                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                     NovAIC VM Runtime                          │  │
│  │          Ubuntu 24.04 (QEMU) + XFCE + VNC + SSH               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Packages

| Package | Description | Path |
|---------|-------------|------|
| **[novaic-core](packages/novaic-core)** | MCP tool server with 44+ tools | `packages/novaic-core` |
| **[novaic-agent](packages/novaic-agent)** | LLM agent framework with tool calling | `packages/novaic-agent` |
| **[novaic-app](packages/novaic-app)** | Desktop client (Tauri + React + VNC) | `packages/novaic-app` |
| **[novaic-cloud](packages/novaic-cloud)** | Cloud service (auth, subscription, LLM proxy) | `packages/novaic-cloud` |
| **[novaic-vm](packages/novaic-vm)** | QEMU VM runtime with Ubuntu desktop | `packages/novaic-vm` |

## MCP Tools

### Desktop Control
| Tool | Description |
|------|-------------|
| `screenshot` | Capture screen with optional grid coordinates |
| `mouse` | Move, click, drag, scroll |
| `keyboard` | Type text, hotkeys, key combinations |

### Browser Automation
| Tool | Description |
|------|-------------|
| `browser_navigate` | Navigate to URL |
| `browser_click` | Click element by selector |
| `browser_type` | Type into input fields |
| `browser_screenshot` | Capture browser viewport |
| `browser_scroll` | Scroll page |
| `browser_eval` | Execute JavaScript |

### Shell Execution
| Tool | Description |
|------|-------------|
| `run_command` | Execute shell commands |
| `run_python` | Execute Python code |

### File Operations
| Tool | Description |
|------|-------------|
| `read_file` | Read file contents |
| `write_file` | Write to file |
| `list_files` | List directory contents |
| `file_info` | Get file metadata |

### Window Management
| Tool | Description |
|------|-------------|
| `list_windows` | List all windows |
| `focus_window` | Focus a window |
| `launch_app` | Launch application |
| `maximize_window` | Maximize window |
| `close_window` | Close window |

### Memory System
| Tool | Description |
|------|-------------|
| `memory_save` | Save key-value data |
| `memory_recall` | Recall saved data |
| `goal_set` | Set a goal |
| `goal_progress` | Update goal progress |
| `session_state` | Get session state |

### Context Awareness
| Tool | Description |
|------|-------------|
| `system_snapshot` | System overview (CPU, memory, disk, windows) |
| `directory_snapshot` | Analyze project structure |
| `app_state` | Get application state |
| `clipboard_get/set` | Clipboard operations |

## Demo

**AI performs data analysis:**

```
User: Analyze ~/data/sales.csv and create a visualization report

NovAIC:
1. screenshot() → Check current desktop state
2. run_command("python3 -c '...pandas...matplotlib...'") → Process data
3. launch_app("firefox") → Open browser to preview HTML report
4. screenshot() → Confirm report generated
   → Report saved to ~/data/report.html ✅
```

**AI automates GUI operations:**

```
User: Open VS Code and create a new Python project

NovAIC:
1. screenshot() → Locate taskbar
2. mouse(action="click", x=520, y=750) → Click VS Code icon
3. keyboard(action="hotkey", keys=["ctrl", "shift", "n"]) → New window
4. keyboard(action="type", text="main.py") → Create file
5. screenshot() → Confirm project created ✅
```

## Documentation

- [Development Guide](DEVELOPMENT.md) — Local development setup
- [Contributing Guide](CONTRIBUTING.md) — How to contribute
- [Product Vision](docs/novaic-vision.md) — Product positioning and vision
- [Product Requirements](docs/PRD.md) — Detailed requirements document
- [Technical Design](docs/tech-design.md) — Architecture and design
- [Roadmap](docs/novaic-roadmap.md) — Development roadmap

## Requirements

- **macOS** (Apple Silicon or Intel) or **Linux**
- **Python** 3.11+
- **Node.js** 20+
- **Rust** 1.70+ (for desktop app)
- **QEMU** 8.x+ (for VM runtime)
- **8GB+ RAM** (VM uses 4GB)
- **50GB+ disk space**

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>NovAIC</strong> — The AI Computer
</p>
