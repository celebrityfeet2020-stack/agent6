#!/bin/bash
set -e

echo "=== M3 Agent v6.5.4 Starting ==="
echo "Agent API:    http://localhost:8888"
echo "Admin Panel:  http://localhost:8889/admin"
echo "Chatroom UI:  http://localhost:8889/chatroom/"
echo "Health Check: http://localhost:8889/health"
echo ""

# Start Agent API (port 8888)
cd /app/backend
python3 main.py &
AGENT_PID=$!
echo "[Startup] Agent API started (PID: $AGENT_PID)"

# Wait 5 seconds for Agent API to initialize
sleep 5

# Start Admin Panel (port 8889)
python3 admin_app.py &
ADMIN_PID=$!
echo "[Startup] Admin Panel started (PID: $ADMIN_PID)"

echo ""
echo "=== M3 Agent v6.5.4 Started ==="
echo "All services are running"
echo ""

# Wait for both processes
wait $AGENT_PID $ADMIN_PID
