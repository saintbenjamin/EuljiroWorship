// js/ws_obs.js

// WebSocket instance used for OBS overlay communication
let ws;

// Flag to prevent overlapping or redundant connection attempts
let connecting = false;

// Interval timer for sending periodic ping messages
let pingTimer = null;

// Timeout handler used to detect missing pong responses
let pongTimeout = null;
let reconnectTimer = null;

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

    clearTimeout(reconnectTimer);
    reconnectTimer = null;

    // Mark that a connection attempt is in progress
    connecting = true;

    const host = location.hostname || "127.0.0.1";
    let socket;
    try {
        socket = new WebSocket(`ws://${host}:8765/ws`);
        ws = socket;
    } catch (e) {
        console.error("[!] WebSocket construction failed", e);
        connecting = false;
        reconnectTimer = setTimeout(() => connectWebSocket(onSlideJsonString), 3000);
        return;
    }

    // Called when the WebSocket connection is successfully opened
    ws.onopen = () => {
        console.log("[✓] WebSocket connected");

        // Reset connection flag
        connecting = false;

        // Start heartbeat mechanism (ping / pong)
        pingTimer = setInterval(() => {
            if (socket.readyState === WebSocket.OPEN) {
                // Send ping to verify connection health
                socket.send("ping");

                // If pong is not received within the timeout, close the connection
                pongTimeout = setTimeout(() => {
                    console.warn("🧟 pong 응답 없음 → 연결 끊기");
                    socket.close();
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
        if (ws === socket) {
            ws = null;
            reconnectTimer = setTimeout(() => connectWebSocket(onSlideJsonString), 3000);
        }

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
