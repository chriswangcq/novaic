# NovAIC Agent

> LLM Agent Service — Orchestrates AI conversations with tool execution

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

NovAIC Agent is the LLM orchestration layer that connects AI models (Claude, GPT, etc.) with tool execution. It handles:

- **LLM Communication** — Manages conversations with AI models
- **Tool Calling** — Parses and routes tool calls to executors
- **Session Management** — Maintains conversation context
- **VNC Management** — Controls VM desktop visualization

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        NovAIC Agent                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐     ┌────────────────┐     ┌─────────────┐  │
│  │   HTTP API     │────▶│   LLM Client   │────▶│   Claude    │  │
│  │   /api/chat    │     │                │     │   /GPT API  │  │
│  └────────────────┘     └────────────────┘     └─────────────┘  │
│          │                                                       │
│          ▼                                                       │
│  ┌────────────────┐     ┌────────────────┐                      │
│  │  Tool Router   │────▶│  MCP Client    │───▶ NovAIC Core     │
│  │                │     │                │     (44+ Tools)      │
│  └────────────────┘     └────────────────┘                      │
│          │                                                       │
│          ▼                                                       │
│  ┌────────────────┐                                             │
│  │    Session     │                                             │
│  │   Management   │                                             │
│  └────────────────┘                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Installation

```bash
cd novaic-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp env.example .env
# Edit .env with your settings
```

## Configuration

Create a `.env` file or set environment variables:

```bash
# Server
HOST=0.0.0.0
PORT=8080
DEBUG=false

# LLM API
LLM_API_BASE=https://api.anthropic.com
LLM_API_KEY=your-api-key
DEFAULT_MODEL=claude-sonnet-4-20250514

# Executor (MCP Server)
EXECUTOR_URL=http://localhost:8080
```

## Quick Start

```bash
# Start the agent server
python main.py

# Or with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

## API Endpoints

### Chat

```http
POST /api/chat
Content-Type: application/json

{
  "message": "Take a screenshot of the desktop",
  "session_id": "optional-session-id"
}
```

Response (streaming):
```json
{
  "type": "text",
  "content": "I'll take a screenshot for you."
}
{
  "type": "tool_use",
  "tool": "screenshot",
  "arguments": {}
}
{
  "type": "tool_result",
  "result": {"image": "base64..."}
}
```

### Session Management

```http
# Get session state
GET /api/session/{session_id}

# Clear session
DELETE /api/session/{session_id}

# List sessions
GET /api/sessions
```

### VNC Management

```http
# Get VNC connection info
GET /vnc/info

# Start VNC session
POST /vnc/start

# Stop VNC session
POST /vnc/stop
```

### Health Check

```http
GET /
GET /api/health
```

## Project Structure

```
novaic-agent/
├── api/
│   ├── __init__.py
│   ├── routes.py         # Chat and session endpoints
│   ├── schemas.py        # Request/response models
│   └── vnc_routes.py     # VNC management endpoints
├── core/
│   ├── __init__.py
│   ├── agent.py          # Main agent logic
│   ├── llm_client.py     # LLM API client
│   ├── mcp_client.py     # MCP protocol client
│   ├── http_client.py    # HTTP utilities
│   └── session.py        # Session management
├── tools/
│   ├── __init__.py
│   ├── base.py           # Tool base classes
│   └── executor.py       # Tool execution
├── config.py             # Configuration
├── main.py               # Application entry point
├── requirements.txt
└── env.example
```

## Flow Example

1. User sends message: "Open Firefox and go to google.com"
2. Agent sends to LLM with available tools
3. LLM responds with tool calls:
   - `launch_app(app_name="firefox")`
   - `browser_navigate(url="https://google.com")`
4. Agent executes tools via MCP Client → NovAIC Core
5. Results returned to LLM for next action
6. LLM provides final response to user

## Development

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn main:app --reload

# Run tests
pytest

# Format code
black .
isort .
```

## Integration with NovAIC App

The NovAIC desktop app (Tauri) connects to this agent service:

```
NovAIC App (React) 
    → HTTP /api/chat 
    → NovAIC Agent 
    → LLM API + MCP Tools
```

## Multi-Provider LLM Support

NovAIC Agent supports multiple LLM providers out of the box:

| Provider | Models | Configuration |
|----------|--------|---------------|
| **OpenAI** | GPT-4o, GPT-4, o1, o3 | API key + optional custom base URL |
| **Anthropic** | Claude 4, Claude 3.5 | API key |
| **Google** | Gemini 2.0, Gemini 1.5 | API key |
| **Azure OpenAI** | GPT-4, GPT-3.5 deployments | Endpoint + deployment name + API key |
| **OpenAI-compatible** | Any compatible API | Custom base URL + API key |

The agent automatically infers the provider from model name (e.g., `claude-*` → Anthropic, `gpt-*` → OpenAI, `gemini-*` → Google).

### Provider Configuration

Configure via the NovAIC App settings or programmatically:

```python
# Provider configs are set at runtime via InitRequest
{
    "openai_api_key": "sk-...",
    "anthropic_api_key": "sk-ant-...",
    "google_api_key": "AIza...",
    "azure_api_base": "https://{resource}.openai.azure.com",
    "azure_api_key": "...",
    "azure_deployment_name": "gpt-4"
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NBCC_HOST` | `0.0.0.0` | Server host |
| `NBCC_PORT` | `19999` | Server port |
| `NBCC_DEBUG` | `false` | Debug mode |
| `NBCC_DEFAULT_PROVIDER` | `openai` | Default LLM provider |
| `NBCC_DEFAULT_MODEL` | `gpt-4o` | Default model |
| `NBCC_EXECUTOR_URL` | `http://127.0.0.1:8080` | MCP Server URL |
| `NBCC_MAX_ITERATIONS` | `20` | Max agent loop iterations |
| `NBCC_LLM_TIMEOUT` | `300` | LLM request timeout (seconds) |

## License

MIT
