# NovAIC Web

React frontend for NovAIC Gateway. Can run standalone (via Gateway) or in Tauri WebView.

## Quick Start

```bash
# Install dependencies
npm install

# Development (with proxy to Gateway)
npm run dev

# Build for production
npm run build
```

## Architecture

This frontend communicates with the Gateway via:

- **REST API** (`/api/*`) - Configuration, health checks
- **WebSocket** (`/ws/{client_id}`) - Real-time chat

No Tauri dependencies - can run in any browser.

## Building for Gateway

```bash
# Build and copy to Gateway
npm run build
cp -r dist ../novaic-gateway/web/
```

The Gateway serves the built files at `http://127.0.0.1:19999/`.

## Development

### Environment Variables

- `VITE_GATEWAY_URL` - Gateway API URL (default: http://127.0.0.1:19999)
- `VITE_GATEWAY_WS` - Gateway WebSocket URL (default: ws://127.0.0.1:19999/ws)

### Running with Gateway

1. Start Gateway: `cd ../novaic-gateway && ./start.sh`
2. Start dev server: `npm run dev`
3. Open http://localhost:3000

The Vite dev server proxies API/WS requests to the Gateway.

### File Structure

```
src/
├── components/     # React components
├── services/       # API and WebSocket clients
│   ├── api.ts      # REST API client
│   ├── websocket.ts # WebSocket client
│   └── index.ts    # Service exports
├── store/          # Zustand store
├── types/          # TypeScript types
└── App.tsx         # Main app component
```
