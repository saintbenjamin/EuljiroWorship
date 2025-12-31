// js/ws_obs.js

// WebSocket instance used for OBS overlay communication
let ws;

// Flag to prevent overlapping or redundant connection attempts
let connecting = false;

// Interval timer for sending periodic ping messages
let pingTimer = null;

// Timeout handler used to detect missing pong responses
let pongTimeout = null;

/**
 * Establishes a WebSocket connection for OBS overlay updates.
 * Receives slide data as a JSON string and forwards it to the renderer.
 *
 * @param {function} onSlideJsonString
 *        Callback invoked with slide JSON payloads received from the server
 */
function connectWebSocket(onSlideJsonString) {
    // Abort if already connecting or if an active connection exists
    if (connecting || (ws && ws.readyState === WebSocket.OPEN)) return;

    // Mark that a connection attempt is in progress
    connecting = true;

    // Create a WebSocket connection to the local slide server
    ws = new WebSocket(`ws://${location.hostname}:8765/ws`);

    // Called when the WebSocket connection is successfully opened
    ws.onopen = () => {
        console.log("[✓] WebSocket connected");

        // Reset connection flag
        connecting = false;

        // Start heartbeat mechanism (ping / pong)
        pingTimer = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                // Send ping to verify connection health
                ws.send("ping");

                // If pong is not received within the timeout, close the connection
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
        console.warn("[x] WebSocket closed, attempting to reconnect...");

        // Reset connection flag
        connecting = false;

        // Attempt reconnection after a short delay
        setTimeout(() => connectWebSocket(onSlideJsonString), 3000);

        // Clean up heartbeat timers
        clearInterval(pingTimer);
        clearTimeout(pongTimeout);
    };

    // Called when a message is received from the server
    ws.onmessage = (event) => {
        // Handle heartbeat response
        if (event.data === "pong") {
            clearTimeout(pongTimeout);
            return;
        }

        // Forward slide JSON payload to the caller
        onSlideJsonString(event.data);
    };
}