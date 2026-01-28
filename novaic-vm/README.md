# NovAIC VM

> QEMU Linux VM runtime — A complete desktop environment for AI agents

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

NovAIC VM provides a pre-configured Ubuntu virtual machine with a desktop environment (XFCE), VNC server, and the NovAIC MCP Server. It enables AI agents to operate a real computer with persistent storage.

### Features

- **Ubuntu 24.04 LTS** — Stable, well-supported Linux distribution
- **XFCE Desktop** — Lightweight desktop environment
- **VNC Server** — Remote desktop access for visualization
- **SSH Access** — Command-line access for debugging
- **Persistent Storage** — QCOW2 disk images preserve state
- **MCP Server** — Pre-deployed NovAIC Core with 44+ tools

## System Requirements

| Requirement | Minimum |
|-------------|---------|
| **OS** | macOS (Apple Silicon or Intel) |
| **RAM** | 8GB (VM uses 4GB) |
| **Disk** | 50GB free space |
| **Software** | Homebrew |

## Quick Start

### 1. One-Command Setup

```bash
cd novaic-vm
./setup.sh
```

This automatically:
- Installs QEMU and dependencies
- Downloads Ubuntu Cloud Image
- Creates and configures the VM
- Starts the VM

### 2. Wait for Initial Configuration

First boot takes 5-10 minutes for cloud-init setup.

Check progress:
```bash
ssh -p 2222 ubuntu@localhost
# Password: ubuntu

tail -f /var/log/cloud-init-output.log
```

### 3. Deploy MCP Server

```bash
./scripts/deploy.sh
```

### 4. Connect

| Service | Address | Credentials |
|---------|---------|-------------|
| **VNC** | `vnc://localhost:5900` | Password: `novaic` |
| **SSH** | `ssh -p 2222 ubuntu@localhost` | Password: `ubuntu` |
| **MCP** | `http://localhost:8080/sse` | — |

## Management Commands

```bash
# Start VM (foreground with window)
./scripts/start-vm.sh

# Start VM (background/daemon mode)
./scripts/start-vm.sh -d

# Stop VM
./scripts/stop-vm.sh

# Check status
./scripts/status-vm.sh

# Deploy/update MCP Server
./scripts/deploy.sh

# Quick deploy (code only, no deps)
./scripts/deploy-quick.sh

# Reset VM to clean state
./scripts/reset-vm.sh

# Completely remove VM
./scripts/clean-vm.sh
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NOVAIC_VM_MEMORY` | `4096` | VM memory (MB) |
| `NOVAIC_VM_CPUS` | `4` | VM CPU cores |
| `NOVAIC_VNC_PORT` | `5900` | VNC port (host) |
| `NOVAIC_MCP_PORT` | `8080` | MCP Server port (host) |
| `NOVAIC_SSH_PORT` | `2222` | SSH port (host) |

### Custom Ubuntu Mirror

```bash
export UBUNTU_MIRROR="https://mirrors.tuna.tsinghua.edu.cn/ubuntu-cloud-images"
./scripts/create-vm.sh
```

## Using with MCP Clients

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "novaic": {
      "url": "http://localhost:8080/sse"
    }
  }
}
```

### Cursor IDE

The MCP server can be used with Cursor's MCP support for AI-assisted development.

### Any MCP-Compatible Client

The SSE endpoint `http://localhost:8080/sse` follows the MCP protocol specification.

## Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│  macOS Host                                                        │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  QEMU VM (Ubuntu 24.04)                                      │  │
│  │                                                               │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐  │  │
│  │  │   XFCE4     │  │   x11vnc    │  │    NovAIC Core       │  │  │
│  │  │   Desktop   │  │   :5901     │  │    MCP Server :8080  │  │  │
│  │  └─────────────┘  └─────────────┘  └──────────────────────┘  │  │
│  │                                                               │  │
│  └─────────────────────────────────────────────────────────────┘  │
│         ↑                  ↑                    ↑                  │
│    SSH :2222          VNC :5900           MCP :8080               │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  MCP Client (Claude Desktop / Cursor / etc)                  │  │
│  │  → MCP Protocol → http://localhost:8080/sse                  │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
novaic-vm/
├── setup.sh              # One-command setup script
├── scripts/
│   ├── create-vm.sh      # Create VM from cloud image
│   ├── start-vm.sh       # Start VM
│   ├── stop-vm.sh        # Stop VM
│   ├── status-vm.sh      # Check VM status
│   ├── deploy.sh         # Deploy MCP Server
│   ├── deploy-quick.sh   # Quick deploy (code only)
│   ├── reset-vm.sh       # Reset to clean state
│   └── clean-vm.sh       # Remove VM completely
├── config/
│   ├── cloud-init.yaml   # cloud-init configuration
│   ├── user-data         # Generated user-data
│   └── meta-data         # Generated meta-data
├── images/               # VM disk images (QCOW2)
├── iso/                  # Ubuntu Cloud Image + seed ISO
└── firmware/             # UEFI firmware (ARM64)
```

## Troubleshooting

### VNC Shows Black Screen

```bash
ssh -p 2222 ubuntu@localhost
sudo systemctl restart lightdm
sudo systemctl restart x11vnc
```

### MCP Server Not Responding

```bash
# Check service status
ssh -p 2222 ubuntu@localhost
sudo systemctl status novaic
sudo journalctl -u novaic -f

# Redeploy
cd novaic-vm
./scripts/deploy.sh
```

### VM Won't Start

```bash
# Check if another instance is running
./scripts/status-vm.sh

# Stop any existing instance
./scripts/stop-vm.sh

# Try starting again
./scripts/start-vm.sh
```

### Port Already in Use

```bash
# Check what's using the port
lsof -i :5900
lsof -i :8080
lsof -i :2222

# Kill the process or use different ports
NOVAIC_VNC_PORT=5901 NOVAIC_MCP_PORT=8082 ./scripts/start-vm.sh
```

### Reset Everything

```bash
# Stop VM
./scripts/stop-vm.sh

# Remove all VM data
./scripts/clean-vm.sh

# Start fresh
./setup.sh
```

## Pre-installed Software

The VM comes with:

- **Desktop**: XFCE4, Thunar file manager
- **Browsers**: Firefox
- **Development**: Python 3.11, pip, Node.js 20, npm
- **Editors**: nano, vim
- **Tools**: git, curl, wget, htop, tmux
- **Automation**: Playwright, xdotool, scrot

## Network Ports

| Port (Host) | Port (VM) | Service |
|-------------|-----------|---------|
| 5900 | 5901 | VNC |
| 2222 | 22 | SSH |
| 8080 | 8080 | MCP Server |

## License

MIT
