<p align="center">
  <img src="novaic-app/public/icon.svg" width="120" alt="NovAIC Logo">
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
| **Multi-Provider LLM** | OpenAI, Anthropic, Google, Azure, or any OpenAI-compatible API |
| **Open Source** | MIT license, fully customizable |

## Installation Guide

### Prerequisites

Before installing NovAIC, ensure you have the following:

| Requirement | Version | Check Command |
|-------------|---------|---------------|
| **macOS** | Apple Silicon or Intel | — |
| **Homebrew** | Latest | `brew --version` |
| **Python** | 3.11+ | `python3 --version` |
| **Node.js** | 20+ | `node --version` |
| **Rust** | 1.70+ | `rustc --version` |
| **RAM** | 8GB+ | — |
| **Disk** | 50GB+ free | — |

### Step 1: Clone the Repository

```bash
git clone https://github.com/chriswangcq/novaic.git
cd novaic
```

### Step 2: Setup the Virtual Machine

The VM provides a persistent Linux desktop environment for AI agents.

```bash
cd novaic-vm
./setup.sh
```

This script will:
- Install QEMU and dependencies via Homebrew
- Download Ubuntu 24.04 Cloud Image
- Create and configure the VM (4GB RAM, 4 CPUs)
- Start the VM

**Wait for initial configuration** (5-10 minutes on first boot):

```bash
# Monitor progress
ssh -p 2222 ubuntu@localhost  # Password: ubuntu
tail -f /var/log/cloud-init-output.log
```

### Step 3: Deploy MCP Server to VM

```bash
./scripts/deploy.sh
```

This deploys NovAIC Core (MCP Server) into the VM. After deployment:

| Service | Address | Credentials |
|---------|---------|-------------|
| **VNC** | `vnc://localhost:5900` | Password: `novaic` |
| **SSH** | `ssh -p 2222 ubuntu@localhost` | Password: `ubuntu` |
| **MCP** | `http://localhost:8080/mcp` | — |

### Step 4: Setup the Desktop App (Optional)

If you want to use the NovAIC desktop application:

```bash
# Setup Gateway (Python backend)
cd novaic-gateway
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup App (frontend + Tauri)
cd ../novaic-app
npm install

# Start development mode
npm run tauri dev
```

The Tauri app will automatically manage Gateway and VM lifecycle.

#### Build for Distribution

```bash
# Build Gateway binary (PyInstaller)
cd novaic-gateway
./venv/bin/python build.py

# Copy to Tauri resources
cp dist/novaic-gateway ../novaic-app/src-tauri/resources/

# Build Tauri app
cd ../novaic-app
npm run tauri build
```

Or use the all-in-one build script:

```bash
./build.sh
```

### Step 5: Configure Your MCP Client

#### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "novaic": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

#### Cursor IDE

Add to your MCP settings:

```json
{
  "novaic": {
    "url": "http://localhost:8080/mcp"
  }
}
```

---

## Quick Start (MCP Server Only)

If you just want to use NovAIC as an MCP server:

```bash
# 1. Setup VM
cd novaic-vm
./setup.sh

# 2. Deploy MCP Server
./scripts/deploy.sh

# 3. Connect your MCP client to http://localhost:8080/mcp
```

## Quick Start (Python Package)

```bash
pip install novaic-core
novaic serve
```

---

## VM Management Commands

```bash
cd novaic-vm

# Start/Stop
./scripts/start-vm.sh      # Start VM (foreground)
./scripts/start-vm.sh -d   # Start VM (background)
./scripts/stop-vm.sh       # Stop VM

# Management
./scripts/status-vm.sh     # Check status
./scripts/deploy.sh        # Deploy/update MCP Server
./scripts/deploy-quick.sh  # Quick deploy (code only)

# Reset
./scripts/reset-vm.sh      # Reset to clean state
./scripts/clean-vm.sh      # Remove completely
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
lsof -i :9000  # Agent port
lsof -i :8080  # MCP port
lsof -i :5900  # VNC port

# Kill the process
kill $(lsof -t -i:9000)
```

### MCP Server Not Responding

```bash
# Check service in VM
ssh -p 2222 ubuntu@localhost
sudo systemctl status novaic
sudo journalctl -u novaic -f

# Redeploy
cd novaic-vm
./scripts/deploy.sh
```

### VNC Shows Black Screen

```bash
ssh -p 2222 ubuntu@localhost
sudo systemctl restart lightdm
sudo systemctl restart x11vnc
```

### VM Won't Start

```bash
# Stop any existing instance
./scripts/stop-vm.sh

# Check status
./scripts/status-vm.sh

# Reset if needed
./scripts/reset-vm.sh
./setup.sh
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         NovAIC Platform                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────┐  ┌────────────────────┐   │
│  │           NovAIC App (Tauri)          │  │  Claude Desktop /  │   │
│  │  ┌─────────────┐  ┌───────────────┐  │  │   Cursor / Any     │   │
│  │  │   Web UI    │  │ Gateway Mgmt  │  │  │   MCP Client       │   │
│  │  │  (React)    │  │  (Rust IPC)   │  │  │                    │   │
│  │  └──────┬──────┘  └───────┬───────┘  │  └─────────┬──────────┘   │
│  │         │                 │          │            │              │
│  │         │    Tauri IPC    │          │            │              │
│  │         └────────┬────────┘          │            │              │
│  └──────────────────┼───────────────────┘            │              │
│                     │                                │              │
│                     ▼                                │              │
│  ┌───────────────────────────────────────────────────┼───────────┐  │
│  │                NovAIC Gateway (Python)            │           │  │
│  │           FastAPI + WebSocket + Agent Core        │           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  │           │  │
│  │  │ REST API    │  │  WebSocket  │  │  Agent   │◄─┘           │  │
│  │  │ /api/*      │  │   /ws/*     │  │  Loop    │  MCP Client  │  │
│  │  └─────────────┘  └─────────────┘  └────┬─────┘              │  │
│  └─────────────────────────────────────────┼────────────────────┘  │
│                                            │ MCP Protocol          │
│                                            ▼                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                       NovAIC Core (in VM)                      │  │
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
| **[novaic-core](novaic-core)** | MCP tool server with 44+ tools (runs in VM) | `novaic-core` |
| **[novaic-gateway](novaic-gateway)** | Python Gateway: REST API + WebSocket + Agent | `novaic-gateway` |
| **[novaic-app](novaic-app)** | Desktop client (Tauri + React + VNC) | `novaic-app` |
| **[novaic-web](novaic-web)** | Standalone Web UI (for browser access) | `novaic-web` |
| **[novaic-agent](novaic-agent)** | Legacy agent (deprecated, use gateway) | `novaic-agent` |
| **[novaic-vm](novaic-vm)** | QEMU VM runtime with Ubuntu desktop | `novaic-vm` |

## MCP Tools

### Desktop Control
| Tool | Description |
|------|-------------|
| `screenshot` | Capture screen with coordinate grid overlay |
| `mouse` | Two-phase control: `aim` (position + zoom) → `click/double/scroll` |
| `keyboard` | `type` text or press `key` combinations |

> **Note:** Mouse uses aim-then-execute workflow. First `aim` to position crosshair with zoom, then `click` using the returned `aim_id`.

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
1. screenshot() → Locate taskbar, estimate VS Code icon at (520, 750)
2. mouse(action="aim", x=520, y=750) → Position crosshair, get aim_id
3. mouse(action="click", aim_id="aim_xxx") → Click VS Code icon
4. keyboard(action="key", keys=["ctrl", "shift", "n"]) → New window
5. keyboard(action="type", text="main.py") → Create file
6. screenshot() → Confirm project created ✅
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
