#!/bin/bash
# NovAIC Agent Startup Script
# This script runs inside the virtual machine to start all services

set -e

echo "🚀 Starting NovAIC Agent services..."

# 1. Start VNC Server
echo "📺 Starting VNC Server..."
vncserver :0 -geometry 1280x800 -depth 24 2>/dev/null || true

# 2. Start desktop environment
echo "🖥️ Starting desktop environment..."
export DISPLAY=:0
startxfce4 &
sleep 3

# 3. Create tmux session for visible terminal
echo "📟 Creating Agent terminal session..."
tmux new-session -d -s agent -x 120 -y 30 || true

# 4. Open visible terminal window
echo "💻 Opening terminal window..."
xfce4-terminal --maximize --title="Agent Terminal" \
  --command="tmux attach-session -t agent" &

# 5. Create working directories
echo "📁 Setting up directories..."
mkdir -p /home/user/workspace
mkdir -p /home/user/uploads

# 6. Start Agent HTTP server
echo "🤖 Starting Agent service..."
cd /opt/novaic-agent
python main.py &

echo "✅ All services started!"
echo ""
echo "Services:"
echo "  - VNC Server: :5900"
echo "  - Agent API:  :8080"
echo "  - Tmux Session: agent"
echo ""
echo "Ready to receive commands."

# Keep script running
wait

