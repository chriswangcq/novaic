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

NovAIC provides AI agents with a **persistent, visual desktop environment** — a complete Linux VM with 56+ MCP tools for desktop control, browser automation, file operations, and more.

Unlike temporary sandboxes that reset after each session, NovAIC maintains state across sessions with SQLite-based persistence. Your AI remembers context, keeps files, and continues work exactly where it left off.

### Key Features

| Feature | Description |
|---------|-------------|
| **Full Desktop Control** | 56+ MCP tools for mouse, keyboard, screenshots, window management |
| **Browser Automation** | Navigate, click, type, scroll — AI controls the browser like a human |
| **Multi-Agent System** | Create and manage multiple AI agents, each with isolated VM disk |
| **Persistent State** | SQLite + QCOW2 disk images preserve everything between sessions |
| **MCP Gateway** | Unified entry point aggregating VM + 4 sub-MCP servers via HTTP |
| **Unified Task System** | `task_async` for long-running ops, `task_query` for status/output retrieval |
| **Auto Output Truncation** | Long outputs (>4KB) auto-cached as tasks, queryable via pagination |
| **Self-Scheduling** | Agents can autonomously check inbox, wake on triggers, run micro-agents |
| **Memory System** | Embedded key-value storage + goal tracking for cross-session context |
| **Agent-User Communication** | Embedded chat tools for questions, answers, and notifications |
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

This deploys novaic-vm MCP Server (with 35+ tools) into the VM. After deployment:

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
- Deploy novaic-vm MCP Server (with 32 tools)
- Start the Gateway with 4 sub-MCP servers (24 tools: agent-context, memory, chat, local)
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
┌──────────────────────────────────────────────────────────────────────────────┐
│                            NovAIC Platform                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────┐    ┌─────────────────────────────────┐  │
│  │      NovAIC App (Tauri)          │    │   Claude Desktop / Cursor /    │  │
│  │  Dashboard + Chat + VNC Viewer   │    │        Any MCP Client          │  │
│  │  + Gateway Mgmt (Rust IPC)       │    │                                │  │
│  │  + VM Manager (QEMU)             │    │                                │  │
│  └───────────────┬──────────────────┘    └───────────────┬────────────────┘  │
│                  │                                       │                   │
│                  └───────────────┬───────────────────────┘                   │
│                                  │                                           │
│                                  ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │                    NovAIC Gateway (Python)                             │   │
│  │              FastAPI + SQLite + SSE + Agent Core                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │   │
│  │  │ REST API    │  │    SSE      │  │TaskManager  │  │  EventBus    │  │   │
│  │  │ /api/*      │  │ /sse/chat   │  │ (Unified)   │  │ (Pub/Sub)    │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └──────────────┘  │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │   │
│  │  │                     SQLite Database (Shared)                     │  │   │
│  │  │               messages, tasks, execution_logs                    │  │   │
│  │  └─────────────────────────────────────────────────────────────────┘  │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │   │
│  │  │  QEMU Debug MCP (Optional, host-side, NOVAIC_MCP_QEMUDEBUG)     │  │   │
│  │  └─────────────────────────────────────────────────────────────────┘  │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │                         Per-Agent Resources                            │   │
│  │                                                                        │   │
│  │  ┌─────────────────────────────┐    ┌─────────────────────────────┐   │   │
│  │  │         Agent A             │    │         Agent B             │   │   │
│  │  │  ┌───────────────────────┐  │    │  ┌───────────────────────┐  │   │   │
│  │  │  │  MCP Gateway          │  │    │  │  MCP Gateway          │  │   │   │
│  │  │  │  /agents/{id}/mcp     │  │    │  │  /agents/{id}/mcp     │  │   │   │
│  │  │  │  56 tools aggregated  │  │    │  │  56 tools aggregated  │  │   │   │
│  │  │  └───────────┬───────────┘  │    │  └───────────┬───────────┘  │   │   │
│  │  │  ┌───────────┴───────────┐  │    │  ┌───────────┴───────────┐  │   │   │
│  │  │  │  Sub-MCP Servers      │  │    │  │  Sub-MCP Servers      │  │   │   │
│  │  │  │  /sub-mcp/agent-ctx   │  │    │  │  /sub-mcp/agent-ctx   │  │   │   │
│  │  │  │  /sub-mcp/memory      │  │    │  │  /sub-mcp/memory      │  │   │   │
│  │  │  │  /sub-mcp/chat        │  │    │  │  /sub-mcp/chat        │  │   │   │
│  │  │  │  /sub-mcp/local       │  │    │  │  /sub-mcp/local       │  │   │   │
│  │  │  │  (24 tools total)     │  │    │  │  (24 tools total)     │  │   │   │
│  │  │  └───────────────────────┘  │    │  └───────────────────────┘  │   │   │
│  │  │  ┌───────────────────────┐  │    │  ┌───────────────────────┐  │   │   │
│  │  │  │  QEMU VM              │  │    │  │  QEMU VM              │  │   │   │
│  │  │  │  ┌─────────────────┐  │  │    │  │  ┌─────────────────┐  │  │   │   │
│  │  │  │  │novaic-vm MCP    │  │  │    │  │  │novaic-vm MCP    │  │  │   │   │
│  │  │  │  │ MCP :8080       │  │  │    │  │  │ MCP :8080       │  │  │   │   │
│  │  │  │  │ (32 tools)      │  │  │    │  │  │ (32 tools)      │  │  │   │   │
│  │  │  │  │ Fwd to :20000   │  │  │    │  │  │ Fwd to :20020   │  │  │   │   │
│  │  │  │  └─────────────────┘  │  │    │  │  └─────────────────┘  │  │   │   │
│  │  │  │  disk-a.qcow2         │  │    │  │  disk-b.qcow2         │  │   │   │
│  │  │  │  Ubuntu + XFCE + VNC  │  │    │  │  Ubuntu + XFCE + VNC  │  │   │   │
│  │  │  └───────────────────────┘  │    │  └───────────────────────┘  │   │   │
│  │  └─────────────────────────────┘    └─────────────────────────────┘   │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Multi-Agent Architecture

Each agent runs in an isolated QEMU VM with:

- **Dedicated Disk Image**: `~/.novaic/vms/{agent-id}/disk.qcow2`
- **UEFI Firmware**: Auto-copied from Homebrew QEMU on ARM64
- **Cloud-Init ISO**: Auto-generated with SSH keys for secure access
- **Port Allocation**: 20 ports per agent (Agent 0: 20000-20019, Agent 1: 20020-20039, etc.)
- **MCP Gateway**: Unified entry point at `/agents/{agent-id}/mcp` with 56 tools
- **VM MCP**: 32 tools in VM (desktop, browser, shell, files)
- **Sub-MCP Servers**: 24 tools in 4 independent MCP servers (agent-context, memory, chat, local)
- **HTTP Discovery**: All tools discovered via standard MCP protocol over HTTP
- **Skills**: Centrally managed in Gateway, exposed as MCP resources (`skill://desktop`, etc.)
- **SQLite State**: Persistent state in `~/.novaic/gateway.db`

## Packages

| Package | Description | Path |
|---------|-------------|------|
| **[novaic-gateway](novaic-gateway)** | Control plane: REST API + SSE + ReAct Agent + SQLite + Sub-MCP Servers | `novaic-gateway` |
| **[novaic-app](novaic-app)** | Desktop client (Tauri + React + VNC + Dashboard) | `novaic-app` |
| **[novaic-vm](novaic-vm)** | VM management + MCP server with 32 tools (desktop, browser, shell, files) | `novaic-vm` |

**Sub-MCP Servers** (mounted at `/agents/{agent_id}/sub-mcp/{name}/`):

| Server | Description | Tools |
|--------|-------------|-------|
| `agent-context` | Context management, inbox, rest state, sub-agent delegation | 6 |
| `memory` | Key-value storage, goals, task history | 10 |
| `chat` | Agent↔User communication | 6 |
| `local` | Web search and fetch | 2 |

All sub-MCP servers are discovered via HTTP using standard MCP protocol, same as VM MCP.

**Legacy/Reference** (source code available but not run as separate processes):

| Package | Description |
|---------|-------------|
| `novaic-mcp-session` | Original standalone session MCP server |
| `novaic-mcp-memory` | Original standalone memory MCP server |
| `novaic-mcp-chat` | Original standalone chat MCP server |
| `novaic-mcp-local` | Original standalone local MCP server |
| `novaic-mcp-qemudebug` | QEMU debugging (optional, can be enabled) |

## MCP Tools (56 Tools via MCP Gateway)

### MCP Gateway (Unified Entry Point)

The MCP Gateway provides a single endpoint at `/agents/{agent_id}/mcp` with:

| Tool | Description |
|------|-------------|
| `task_async` | Asynchronously execute any MCP tool (returns task_id) |
| `task_query` | Query task status, outputs, results with pagination |
| `task_list` | List all tasks, optionally filtered by status |
| `task_cancel` | Cancel a running task |
| `task_summary` | Get AI-generated summary of completed task |
| `agent_call` | Synchronously delegate complex task to sub-agent |

**Auto Output Truncation**: When any tool returns >4KB output, it's automatically truncated and stored as a `sync_output` task. Use `task_query(task_id, start_line=1, end_line=100)` to retrieve full content.

### novaic-vm MCP Server (VM-based, 32 tools)

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

### Sub-MCP Servers (24 tools via HTTP)

All sub-MCP servers are discovered via standard MCP HTTP protocol, same as VM MCP.

#### Agent Context Tools (6 tools) — `/sub-mcp/agent-context/`
| Tool | Description |
|------|-------------|
| `agent_context_list` | List all agent contexts (main + subagents) |
| `agent_context_history` | Get context message history |
| `agent_context_send` | Send message to a context |
| `agent_inbox` | Check pending events and messages |
| `agent_rest` | Voluntarily enter rest state with wake conditions |

#### Memory Tools (10 tools) — `/sub-mcp/memory/`
| Tool | Description |
|------|-------------|
| `memory_save` | Save key-value data |
| `memory_recall` | Recall saved data |
| `memory_delete` | Delete memory entry |
| `memory_list_namespaces` | List all memory namespaces |
| `task_log` | Log task progress |
| `task_history` | Get task execution history |
| `goal_set` | Set a goal |
| `goal_progress` | Update goal progress |
| `goal_complete` | Mark goal as complete |
| `session_state` | Get/set session state |

#### Chat Tools (6 tools) — `/sub-mcp/chat/`
| Tool | Description |
|------|-------------|
| `chat_reply` | Send reply to user |
| `chat_ask` | Ask user a question |
| `chat_notify` | Send notification to user |
| `chat_show_image` | Display image to user |
| `chat_history` | Get chat history |
| `chat_get_message` | Get specific message |

#### Local Tools (2 tools) — `/sub-mcp/local/`
| Tool | Description |
|------|-------------|
| `web_search` | Search the web |
| `web_fetch` | Fetch web page content |

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

**AI runs long build process:**

```
User: Build the entire project

NovAIC:
1. task_async(tool="run_command", args={"command": "make -j8"}, label="Build")
   → Returns task_id: "abc123"
2. ... continue other work ...
3. task_query(task_id="abc123") → Check progress
   → status: "running", running_seconds: 45
4. task_query(task_id="abc123") → Build complete
   → status: "completed", result: {exit_code: 0, stdout: "...[truncated]...", stdout_task_id: "so_xyz"}
5. task_query(task_id="so_xyz", tail_lines=50) → Get build output
   → Build successful ✅
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
All agent state (messages, execution logs, tasks, configuration) is persisted in SQLite database at `~/.novaic/gateway.db`. This enables:
- Stateless architecture (Gateway can restart without losing state)
- Cross-session persistence
- Efficient querying and filtering
- Transaction safety

### Unified Task System
Long-running operations and large outputs are managed through a unified task system:

```
┌─────────────────────────────────────────────────────────────┐
│                    Unified Task Manager                      │
│                    (SQLite + Output Files)                   │
│                                                              │
│  task_async    → Async execution of any MCP tool            │
│  task_query    → Query status/output with pagination        │
│  task_list     → List tasks by status                       │
│  task_cancel   → Cancel running task                        │
│  task_summary  → AI-generated result summary                │
│                                                              │
│  Types: sync_output (24h TTL) | tool/agent (7d TTL)         │
│  Storage: SQLite metadata + files for large outputs         │
└─────────────────────────────────────────────────────────────┘
```

**Auto Truncation**: When any tool returns >4KB output:
1. Output is automatically truncated (first 1.5KB + last 1.5KB)
2. Full content is saved to file
3. Returns `task_id` for later retrieval via `task_query`

Example:
```python
# Long output auto-truncated
result = run_command("cat large_file.txt")
# Returns: {"stdout": "...[truncated]...", "stdout_task_id": "so_abc123"}

# Retrieve full content with pagination
task_query(task_id="so_abc123", start_line=1, end_line=100)
task_query(task_id="so_abc123", tail_lines=50)
```

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
- Aggregates 32 tools from VM MCP server via HTTP
- Aggregates 24 tools from 4 sub-MCP servers via HTTP
- Unified HTTP discovery for all MCP servers
- Auto-discovery with periodic health checks
- Supports both port and URL registration

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
