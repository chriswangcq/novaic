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

NovAIC provides AI agents with a **persistent, visual desktop environment** — a complete Linux VM with 35+ MCP tools for desktop control, browser automation, file operations, and more.

Unlike temporary sandboxes that reset after each session, NovAIC maintains state across sessions with SQLite-based persistence. Your AI remembers context, keeps files, and continues work exactly where it left off.

### Key Features

| Feature | Description |
|---------|-------------|
| **Full Desktop Control** | 35+ MCP tools for mouse, keyboard, screenshots, window management |
| **Browser Automation** | Navigate, click, type, scroll — AI controls the browser like a human |
| **Multi-Agent System** | Create and manage multiple AI agents, each with isolated VM disk |
| **Persistent State** | SQLite + QCOW2 disk images preserve everything between sessions |
| **Self-Scheduling** | Agents can autonomously check inbox, wake on triggers, run micro-agents |
| **Memory System** | Host-based key-value storage + goal tracking for cross-session context |
| **Agent-User Communication** | Dedicated MCP server for questions, answers, and notifications |
| **Event-Driven Architecture** | EventBus with publish/subscribe for system-wide event handling |
| **Context Awareness** | System snapshots, directory analysis, app state detection |
| **Privacy First** | Runs locally in QEMU VM — your data never leaves your machine |
| **Multi-Provider LLM** | OpenAI, Anthropic, Google, Azure, or any OpenAI-compatible API |
| **Graceful VM Lifecycle** | Automatic UEFI/cloud-init setup, graceful shutdown via SSH |
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

This deploys novaic-mcp-vmuse (MCP Server with 35+ tools) into the VM. After deployment:

| Service | Address | Credentials |
|---------|---------|-------------|
| **VNC** | `vnc://localhost:5900` | Password: `novaic` |
| **SSH** | `ssh -p 2222 ubuntu@localhost` | Password: `ubuntu` |
| **MCP** | `http://localhost:8080/mcp` | — |

### Step 4: Setup the Desktop App (Recommended)

The NovAIC desktop application provides a complete GUI experience with multi-agent management:

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

**Key Features of Desktop App:**

- **Onboarding Flow**: First-time setup wizard for creating your first agent
- **Agent Selector**: Switch between multiple AI agents (each has isolated VM)
- **VNC Viewer**: Built-in visual access to the VM desktop
- **Auto Lifecycle**: Tauri manages Gateway and VM startup/shutdown automatically
- **Graceful Shutdown**: VMs shut down cleanly via SSH before force-kill

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

## Quick Start (Desktop App — Recommended)

The easiest way to get started with full multi-agent support:

```bash
# 1. Clone and build
git clone https://github.com/chriswangcq/novaic.git
cd novaic
./build.sh

# 2. Run the app
open novaic-app/src-tauri/target/release/bundle/macos/NovAIC.app

# 3. Follow the onboarding wizard to create your first agent
```

The app will automatically:
- Download Ubuntu cloud image
- Create VM with UEFI and cloud-init
- Deploy novaic-mcp-vmuse (MCP Server)
- Start 5 host-based MCP servers (session, memory, chat, local, qemudebug)
- Start the VM and connect VNC

## Quick Start (MCP Server Only)

If you just want to use NovAIC as an MCP server without the desktop app:

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

## VM Management

### Desktop App (Automatic)

When using the desktop app, VM lifecycle is fully managed:

- **Start**: VM starts when you select an agent or complete onboarding
- **Stop**: Graceful shutdown (SSH poweroff → wait → force kill)
- **Cleanup**: VmManager Drop trait ensures cleanup on app exit

### Manual Commands

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
lsof -i :19999  # Gateway port
lsof -i :8080  # MCP port
lsof -i :5900  # VNC port

# Kill the process
kill $(lsof -t -i:19999)
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
┌─────────────────────────────────────────────────────────────────────────┐
│                         NovAIC Platform                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────┐  ┌────────────────────┐       │
│  │        NovAIC App (Tauri)             │  │  Claude Desktop /  │       │
│  │  ┌─────────────┐  ┌───────────────┐  │  │   Cursor / Any     │       │
│  │  │  Dashboard  │  │ Gateway Mgmt  │  │  │   MCP Client       │       │
│  │  │  + Chat UI  │  │  (Rust IPC)   │  │  │                    │       │
│  │  │  + VNC View │  │ + VM Manager  │  │  │                    │       │
│  │  │             │  │   (QEMU)      │  │  │                    │       │
│  │  └──────┬──────┘  └───────┬───────┘  │  └─────────┬──────────┘       │
│  │         │                 │          │            │                  │
│  │         │    Tauri IPC    │          │            │                  │
│  │         └────────┬────────┘          │            │                  │
│  └──────────────────┼───────────────────┘            │                  │
│                     │                                │                  │
│                     ▼                                │                  │
│  ┌───────────────────────────────────────────────────┼───────────────┐  │
│  │              NovAIC Gateway (Python)              │               │  │
│  │        FastAPI + SQLite + SSE + Agent Core        │               │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  │               │  │
│  │  │ REST API    │  │     SSE     │  │  Agent   │◄─┘               │  │
│  │  │ /api/*      │  │ /sse/chat   │  │  ReAct   │  MCP Clients     │  │
│  │  └─────────────┘  └─────────────┘  └────┬─────┘                  │  │
│  │  ┌─────────────────────────────────────┐ │                        │  │
│  │  │        ToolRegistry (Aggregator)     │ │                        │  │
│  │  │  Routes to: vmuse, session, memory,  │ │                        │  │
│  │  │             chat, local, qemudebug   │ │                        │  │
│  │  └──────────────────┬──────────────────┘ │                        │  │
│  │  ┌─────────────────────────────────────┐ │                        │  │
│  │  │    EventBus (Publish/Subscribe)      │ │                        │  │
│  │  │  Events: message, tool, wake, etc.   │ │                        │  │
│  │  └─────────────────────────────────────┘ │                        │  │
│  │  ┌─────────────────────────────────────┐ │                        │  │
│  │  │      SQLite Database (State)         │ │                        │  │
│  │  │  messages, execution_logs, config    │ │                        │  │
│  │  └─────────────────────────────────────┘ │                        │  │
│  └──────────────────────────────────────────┼────────────────────────┘  │
│                                             │ HTTP to MCP Servers       │
│  ┌──────────────────────────────────────────┼────────────────────────┐  │
│  │                Host MCP Servers          │                        │  │
│  │  ┌─────────────────┐ ┌────────────────┐ │                        │  │
│  │  │ novaic-mcp-     │ │ novaic-mcp-    │ │                        │  │
│  │  │ session         │ │ memory         │ │                        │  │
│  │  │ :20001          │ │ :20002         │ │                        │  │
│  │  └─────────────────┘ └────────────────┘ │                        │  │
│  │  ┌─────────────────┐ ┌────────────────┐ │                        │  │
│  │  │ novaic-mcp-     │ │ novaic-mcp-    │ │                        │  │
│  │  │ chat            │ │ local          │ │                        │  │
│  │  │ :20003          │ │ :20004         │ │                        │  │
│  │  └─────────────────┘ └────────────────┘ │                        │  │
│  │  ┌─────────────────┐                    │                        │  │
│  │  │ novaic-mcp-     │                    │                        │  │
│  │  │ qemudebug       │                    │                        │  │
│  │  │ :20005          │                    │                        │  │
│  │  └─────────────────┘                    │                        │  │
│  └──────────────────────────────────────────┼────────────────────────┘  │
│                                             │ Port Forward            │
│  ┌──────────────────────────────────────────┼────────────────────────┐  │
│  │                  Per-Agent VMs           ▼                        │  │
│  │  ┌────────────────────────┐    ┌────────────────────────┐        │  │
│  │  │  Agent A VM            │    │  Agent B VM            │  ...   │  │
│  │  │  ┌──────────────────┐  │    │  ┌──────────────────┐  │        │  │
│  │  │  │ novaic-mcp-vmuse │  │    │  │ novaic-mcp-vmuse │  │        │  │
│  │  │  │ MCP :8080        │  │    │  │ MCP :8080        │  │        │  │
│  │  │  │ (35+ Tools)      │  │    │  │ (35+ Tools)      │  │        │  │
│  │  │  │ Fwd to :20000    │  │    │  │ Fwd to :20020    │  │        │  │
│  │  │  └──────────────────┘  │    │  └──────────────────┘  │        │  │
│  │  │  disk-a.qcow2          │    │  disk-b.qcow2          │        │  │
│  │  │  Ubuntu 24.04 + XFCE   │    │  Ubuntu 24.04 + XFCE   │        │  │
│  │  │  + VNC + SSH           │    │  + VNC + SSH           │        │  │
│  │  └────────────────────────┘    └────────────────────────┘        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Multi-Agent Architecture

Each agent runs in an isolated QEMU VM with:

- **Dedicated Disk Image**: `~/.novaic/vms/{agent-id}/disk.qcow2`
- **UEFI Firmware**: Auto-copied from Homebrew QEMU on ARM64
- **Cloud-Init ISO**: Auto-generated with SSH keys for secure access
- **Port Allocation**: 20 ports per agent (Agent 0: 20000-20019, Agent 1: 20020-20039, etc.)
- **MCP Servers**: 6 MCP servers (1 in VM + 5 on host) per agent
- **SQLite State**: Persistent state in `~/.novaic/gateway.db`

## Packages

| Package | Description | Path |
|---------|-------------|------|
| **[novaic-gateway](novaic-gateway)** | Control plane: REST API + SSE + ReAct Agent + SQLite | `novaic-gateway` |
| **[novaic-app](novaic-app)** | Desktop client (Tauri + React + VNC + Dashboard) | `novaic-app` |
| **[novaic-mcp-vmuse](novaic-mcp-vmuse)** | VM-based MCP server with 35+ tools (desktop, browser, shell, files) | `novaic-mcp-vmuse` |
| **[novaic-mcp-session](novaic-mcp-session)** | Host-based session management MCP server | `novaic-mcp-session` |
| **[novaic-mcp-memory](novaic-mcp-memory)** | Host-based memory system MCP server (key-value + goals) | `novaic-mcp-memory` |
| **[novaic-mcp-chat](novaic-mcp-chat)** | Agent↔User communication MCP server (questions, answers, notifications) | `novaic-mcp-chat` |
| **[novaic-mcp-local](novaic-mcp-local)** | Host-based local file access MCP server | `novaic-mcp-local` |
| **[novaic-mcp-qemudebug](novaic-mcp-qemudebug)** | QEMU debugging and VM inspection MCP server | `novaic-mcp-qemudebug` |
| **[novaic-vm](novaic-vm)** | QEMU VM runtime with Ubuntu desktop | `novaic-vm` |
| **[novaic-web](novaic-web)** | Standalone Web UI (for browser access) | `novaic-web` |
| **[novaic-agent](novaic-agent)** | Legacy standalone agent (deprecated, migrated to gateway) | `novaic-agent` |

## MCP Tools (35+ Tools across 6 MCP Servers)

### novaic-mcp-vmuse (VM-based, 35+ tools)

#### Desktop Control
| Tool | Description |
|------|-------------|
| `screenshot` | Capture screen with coordinate grid overlay |
| `mouse` | Two-phase control: `aim` (position + zoom) → `click/double/scroll` |
| `keyboard` | `type` text or press `key` combinations |

> **Note:** Mouse uses aim-then-execute workflow. First `aim` to position crosshair with zoom, then `click` using the returned `aim_id`.

#### Browser Automation
| Tool | Description |
|------|-------------|
| `browser_navigate` | Navigate to URL |
| `browser_click` | Click element by selector |
| `browser_type` | Type into input fields |
| `browser_screenshot` | Capture browser viewport |
| `browser_scroll` | Scroll page |
| `browser_eval` | Execute JavaScript |

#### Shell Execution
| Tool | Description |
|------|-------------|
| `run_command` | Execute shell commands with timeout |
| `run_python` | Execute Python code in subprocess |
| `run_code` | Execute code in various languages |

#### File Operations
| Tool | Description |
|------|-------------|
| `read_file` | Read file contents |
| `write_file` | Write to file |
| `list_files` | List directory contents |
| `file_info` | Get file metadata |
| `search_files` | Search files by pattern |

#### Window Management
| Tool | Description |
|------|-------------|
| `list_windows` | List all windows |
| `focus_window` | Focus a window |
| `launch_app` | Launch application |
| `maximize_window` | Maximize window |
| `close_window` | Close window |

#### Context Awareness
| Tool | Description |
|------|-------------|
| `system_snapshot` | System overview (CPU, memory, disk, windows) |
| `directory_snapshot` | Analyze project structure |
| `app_state` | Get application state |
| `clipboard_get/set` | Clipboard operations |

### novaic-mcp-session (Host-based)
| Tool | Description |
|------|-------------|
| `session_list` | List all sessions |
| `session_get` | Get session details |
| `session_create` | Create new session |
| `session_messages` | Get session messages |

### novaic-mcp-memory (Host-based)
| Tool | Description |
|------|-------------|
| `memory_save` | Save key-value data |
| `memory_recall` | Recall saved data |
| `memory_delete` | Delete memory entry |
| `memory_list` | List all memory keys |
| `goal_set` | Set a goal |
| `goal_get` | Get goal status |
| `goal_progress` | Update goal progress |
| `goal_complete` | Mark goal as complete |

### novaic-mcp-chat (Host-based)
| Tool | Description |
|------|-------------|
| `ask_user` | Ask user a question and wait for answer |
| `notify_user` | Send notification to user |
| `chat_history` | Get chat history with user |

### novaic-mcp-local (Host-based)
| Tool | Description |
|------|-------------|
| `local_read_file` | Read file from host machine |
| `local_write_file` | Write file to host machine |
| `local_list_files` | List files on host machine |
| `local_execute` | Execute command on host |

### novaic-mcp-qemudebug (Host-based)
| Tool | Description |
|------|-------------|
| `qemu_status` | Get QEMU VM status |
| `qemu_info` | Get VM information |
| `ssh_exec` | Execute command via SSH |
| `port_check` | Check if port is accessible |

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

## Key Features Explained

### SQLite-Based State Management
All agent state (messages, execution logs, configuration) is persisted in SQLite database at `~/.novaic/gateway.db`. This enables:
- Stateless architecture (Gateway can restart without losing state)
- Cross-session persistence
- Efficient querying and filtering
- Transaction safety

### Server-Sent Events (SSE)
Real-time updates from Gateway to UI via SSE (`/sse/chat/{agent_id}`):
- Replaces WebSocket with simpler HTTP-based streaming
- Auto-reconnection support
- Message types: `user`, `assistant`, `tool_call`, `tool_result`, `error`, `thinking`

### Agent Self-Scheduling
Agents can autonomously manage their workflow:
- **Inbox**: Check for pending events (questions, notifications, tasks)
- **Wake Triggers**: Schedule future actions (cron-like, webhook, keyword-based)
- **Micro Agents**: Lightweight rule-based agents for filtering and routing
- **Sub-Agents**: Delegate subtasks to specialized agents

### ToolRegistry (Unified Tool Management)
Single entry point for all MCP tools:
- Aggregates tools from 6 MCP servers
- Auto-discovery and registration
- Health checks and reconnection
- Conflict resolution (priority-based)

### EventBus (Publish/Subscribe)
System-wide event handling:
- Event types: `USER_MESSAGE`, `TOOL_START`, `TOOL_END`, `WAKE_TRIGGER`, etc.
- Subscribers: WakeController, MicroAgentEngine, SessionManager, etc.
- Priority-based event processing
- Async event handlers

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
