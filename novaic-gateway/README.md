# NovAIC Gateway

Unified control plane for the NovAIC AI Agent. Provides REST API, WebSocket, and serves the Web UI.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 NovAIC Gateway (Python)                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │                FastAPI Server                     │  │
│  │  - /api/*      REST API                          │  │
│  │  - /ws/*       WebSocket (real-time chat)        │  │
│  │  - /*          Static files (Web UI)             │  │
│  └──────────────────────────────────────────────────┘  │
│                         │                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Agent     │  │   Config    │  │    MCP      │     │
│  │   (LLM)     │  │   (JSON)    │  │   Client    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
        │
        │ MCP (JSON-RPC)
        ▼
┌───────────────────────────────────────────────────────┐
│            novaic-core (MCP Server)                   │
│      Desktop, Browser, File, Memory tools            │
└───────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Start Gateway
./start.sh

# Or manually:
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Gateway runs on http://127.0.0.1:19999 by default.

## Configuration

Configuration is stored in `$NOVAIC_DATA_DIR/config.json`. On macOS, this is typically `~/Library/Application Support/com.novaic.app/config.json` when running through the NovAIC app.

You can configure:

- API keys (OpenAI, Anthropic, Google, Azure, OpenAI-compatible)
- Available models
- Default model
- Max tokens and iterations

## API Endpoints

### REST API

- `GET /api/health` - Health check
- `GET /api/config` - Get configuration (public version)
- `PATCH /api/config/settings` - Update settings
- `POST /api/config/api-keys` - Add API key
- `PATCH /api/config/api-keys/{id}` - Update API key
- `DELETE /api/config/api-keys/{id}` - Delete API key
- `POST /api/chat` - Chat (non-streaming)
- `POST /api/chat/stream` - Chat (SSE streaming)
- `POST /api/clear` - Clear history
- `POST /api/interrupt` - Interrupt execution

### WebSocket

Connect to `ws://127.0.0.1:19999/ws/{client_id}` for real-time chat.

**Client -> Server:**
```json
{"type": "chat", "message": "...", "model": "...", "mode": "agent|chat"}
{"type": "interrupt"}
{"type": "clear"}
{"type": "ping"}
```

**Server -> Client:**
```json
{"type": "thinking", "data": "...", "timestamp": "..."}
{"type": "tool_start", "data": {...}, "timestamp": "..."}
{"type": "tool_end", "data": {...}, "timestamp": "..."}
{"type": "final", "data": "...", "timestamp": "..."}
{"type": "error", "data": {...}, "timestamp": "..."}
{"type": "pong", "data": null, "timestamp": "..."}
```

## Environment Variables

- `NOVAIC_HOST` - Host to bind to (default: 127.0.0.1)
- `NOVAIC_PORT` - Port to listen on (default: 19999)
- `NOVAIC_DEBUG` - Enable debug mode (default: false)

## Development

### Building the Web UI

```bash
# Web UI is now part of novaic-app
cd ../novaic-app
npm install
npm run build
cp -r dist ../novaic-gateway/web/
```

### Running with Tauri

The simplified Tauri app (`novaic-app`) acts as a lightweight WebView wrapper:

1. Start the Gateway: `./start.sh`
2. Start Tauri: `cd ../novaic-app && npm run tauri dev`

The Tauri app loads `http://127.0.0.1:19999` directly.
