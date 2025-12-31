// js/ws_hall.js

// WebSocket instance used for communication with the server
let ws;

// Flag to prevent multiple simultaneous connection attempts
let connecting = false;

// Interval timer for sending periodic ping messages
let pingTimer = null;

// Timeout handler for detecting missing pong responses
let pongTimeout = null;

/**
 * Establishes a WebSocket connection to the hall overlay server.
 * Automatically handles reconnection and heartbeat (ping/pong).
 *
 * @param {function} onMessage - Callback invoked with non-control messages from the server
 */
function connectWebSocket(onMessage) {
    // Abort if a connection attempt is already in progress
    if (connecting) return;

    // Mark connection attempt as active
    connecting = true;

    // Create a new WebSocket connection to the local server
    ws = new WebSocket(`ws://${location.hostname}:8765/ws`);

    // Called when the WebSocket connection is successfully opened
    ws.onopen = () => {
        console.log("[✓] WebSocket connected");

        // Reset connection flag
        connecting = false;

        // Start periodic ping messages to keep the connection alive
        pingTimer = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                // Send heartbeat ping
                ws.send("ping");

                // Set a timeout to detect missing pong responses
                pongTimeout = setTimeout(() => {
                    console.warn("🧟 pong 응답 없음 → 연결 끊기");
                    ws.close();
                }, 5000);
            }
        }, 30000);
    };

    // Called when a WebSocket error occurs
    ws.onerror = e => {
        console.error("[!] WebSocket error", e);

        // Allow reconnection attempts after an error
        connecting = false;
    };

    // Called when the WebSocket connection is closed
    ws.onclose = () => {
        console.warn("[x] WebSocket closed, reconnecting...");

        // Reset connection flag
        connecting = false;

        // Clean up timers related to heartbeat handling
        clearInterval(pingTimer);
        clearTimeout(pongTimeout);

        // Attempt to reconnect after a short delay
        setTimeout(() => connectWebSocket(onMessage), 3000);
    };

    // Called when a message is received from the server
    ws.onmessage = event => {
        // Handle heartbeat response
        if (event.data === "pong") {
            clearTimeout(pongTimeout);
            return;
        }

        // Forward application-level messages to the caller
        onMessage(event.data);
    };
}