#!/bin/sh

# 1. Start tailscaled in userspace mode exposing a local SOCKS5 server on port 1055
echo "Starting tailscaled in userspace mode..."
tailscaled --tun=userspace-networking --socks5-server=localhost:1055 --state=mem: &

# Wait for tailscaled daemon to boot
sleep 3

# 2. If TAILSCALE_AUTHKEY is provided, authenticate and connect to your tailnet
if [ -n "$TAILSCALE_AUTHKEY" ]; then
    echo "Connecting to Tailscale network..."
    
    # If a Tailscale Exit Node is provided (your Raspberry Pi), route all outbound traffic through it
    if [ -n "$TAILSCALE_EXIT_NODE" ]; then
        echo "Configuring exit node routing through: $TAILSCALE_EXIT_NODE"
        tailscale up --authkey="$TAILSCALE_AUTHKEY" --exit-node="$TAILSCALE_EXIT_NODE" --exit-node-allow-lan-access=true --hostname=pinseeker-gcp
    else
        tailscale up --authkey="$TAILSCALE_AUTHKEY" --hostname=pinseeker-gcp
    fi
else
    echo "No TAILSCALE_AUTHKEY found. Skipping Tailscale connection."
fi

# 3. Start the FastAPI web application
echo "Starting PinSeeker FastAPI server on port $PORT..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
