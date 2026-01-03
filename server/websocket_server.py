# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/server/websocket_server.py

WebSocket server for broadcasting slide data using aiohttp with resilient error handling.

This module runs an aiohttp-based WebSocket server that listens for slide JSON messages and broadcasts them to all connected clients in real time.

Features:

- Real-time broadcast to multiple connected clients
- Ping/pong heartbeat handling
- Error isolation per client connection
- Automatic cleanup of disconnected ("zombie") clients

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

import json
import logging
import asyncio
from aiohttp import web, WSMsgType

# ─────────────────────────────
# Logging setup
logger = logging.getLogger("slide_socket_server")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)

# ─────────────────────────────
# Connected clients set
connected_clients = set()

async def websocket_handler(request):
    """
    Handle a single WebSocket client connection.

    The handler:
      - upgrades the incoming HTTP request to a WebSocket
      - registers the client in the global client set
      - responds to heartbeat "ping" messages with "pong"
      - attempts to parse incoming text frames as JSON and broadcast them
      - ensures the client is removed and closed on disconnect/errors

    Args:
        request (aiohttp.web.Request): Incoming request for WebSocket upgrade.

    Returns:
        aiohttp.web.WebSocketResponse: The prepared WebSocket response object.
    """
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    connected_clients.add(ws)
    logger.debug("[+] Client connected")

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                if msg.data == "ping":
                    await ws.send_str("pong")
                    continue

                logger.debug("[WS] Received message (ignored): %s", msg.data.encode("ascii", errors="replace").decode())

                try:
                    slide_dict = json.loads(msg.data)
                    await broadcast(slide_dict)
                except Exception as e:
                    logger.error("[!] Failed to broadcast: %s", e, exc_info=True)

            elif msg.type == WSMsgType.ERROR:
                logger.warning("[!] WS connection closed with exception: %s", ws.exception())

    except Exception as e:
        logger.error("[!] Connection error: %s", e, exc_info=True)

    finally:
        connected_clients.discard(ws)
        if not ws.closed:
            await ws.close()
        logger.debug("[-] Client disconnected")

    return ws

async def broadcast(slide_dict):
    """
    Broadcast a slide payload to all currently connected WebSocket clients.

    The payload is JSON-serialized and sent as a text frame. The function
    also performs basic client hygiene:

        - detects and removes closed or errored ("zombie") connections
        - removes clients that fail to receive within a short timeout

    Args:
        slide_dict (dict): Slide payload to broadcast. Must be JSON-serializable.

    Returns:
        None
    """
    if not connected_clients:
        logger.debug("[!] No clients connected")
        return

    message = json.dumps(slide_dict)
    logger.debug("[→] Broadcasting: %s", message)

    for ws in connected_clients.copy():
        if ws.closed or ws.close_code or ws.exception() is not None:
            connected_clients.discard(ws)
            await ws.close()
            logger.warning("🧹 Removed zombie client (closed/code/exception)")
            continue

        try:
            await asyncio.wait_for(ws.send_str(message), timeout=1.5)
        except Exception as e:
            logger.error("[!] Send failed: %s", e, exc_info=True)
            connected_clients.discard(ws)
            await ws.close()
            logger.warning("🧹 Removed client after send failure")

async def on_shutdown(app):
    """
    Close all active WebSocket connections during server shutdown.

    This coroutine is registered to ``app.on_shutdown`` and is expected
    to run when aiohttp is stopping. It attempts to close all active client
    sockets with a normal "going away" code.

    Args:
        app (aiohttp.web.Application): The aiohttp application instance.

    Returns:
        None
    """
    # Snapshot first to avoid "Set changed size during iteration"
    clients = list(connected_clients)

    logger.info("[⇓] Server shutting down: closing %d clients", len(connected_clients))


    # Close sockets best-effort; never hang shutdown indefinitely.
    for ws in clients:
        try:
            if not ws.closed:
                await asyncio.wait_for(
                    ws.close(code=1001, message=b"Server shutdown"),
                    timeout=1.0,
                )
        except Exception:
            pass

    connected_clients.clear()

# ─────────────────────────────
# aiohttp Web App setup
app = web.Application()
app.router.add_get("/ws", websocket_handler)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    logger.info("[*] WebSocket server starting on ws://0.0.0.0:8765/ws")
    web.run_app(app, port=8765)